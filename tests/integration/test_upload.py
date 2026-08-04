"""
test_upload.py — Test de integración para la operación CREATE (subir PDF)
=========================================================================
Este test verifica el flujo completo de subida de un documento:
  1. Preparar un PDF fake con magic bytes válidos.
  2. Enviar POST /api/v1/documents/ con el archivo.
  3. Verificar que la respuesta es 201 Created.
  4. Verificar que el documento fue persistido en MongoDB.
  5. Verificar que los campos de la respuesta coinciden con lo enviado.

Estrategia de integración:
  - Usamos MongoDB real (ya corriendo localmente).
  - Usamos httpx.AsyncClient con ASGITransport para hacer requests HTTP a la app FastAPI.
  - Limpiamos la colección "documents" antes y después del test para aislamiento.
  - No usamos mocks: se prueban todas las capas reales (Router → Controller → Service → Repository → MongoDB).
"""

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from beanie import init_beanie

from app.main import app
from app.data.database.mongo_connection import connect, disconnect, get_database
from app.data.models.document_model import DocumentModel


# ------------------------------------------------------------------ #
# Fixtures
# ------------------------------------------------------------------ #

@pytest_asyncio.fixture(scope="function")
async def clean_database():
    """
    Conecta a MongoDB, inicializa Beanie, y limpia la colección documents
    antes de cada test. Se desconecta al final.
    """
    await connect()
    db = get_database()
    await init_beanie(database=db, document_models=[DocumentModel])

    # Limpiar colección antes del test
    await DocumentModel.delete_all()

    yield db

    # Limpiar colección después del test
    await DocumentModel.delete_all()
    await disconnect()


@pytest_asyncio.fixture(scope="function")
async def async_client(clean_database):
    """
    Cliente HTTP async para hacer requests a la app FastAPI.
    Usa ASGITransport para comunicarse directamente con la app sin levantar servidor.
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


@pytest.fixture
def fake_pdf_bytes() -> bytes:
    """
    PDF mínimo pero válido: magic bytes + estructura básica.
    pdfplumber puede abrirlo (aunque no extraerá texto útil).
    """
    return (
        b"%PDF-1.4\n"
        b"1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
        b"2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n"
        b"3 0 obj<</Type/Page/MediaBox[0 0 612 792]>>endobj\n"
        b"xref\n"
        b"0 4\n"
        b"0000000000 65535 f\n"
        b"0000000009 00000 n\n"
        b"0000000052 00000 n\n"
        b"0000000101 00000 n\n"
        b"trailer<</Size 4/Root 1 0 R>>\n"
        b"startxref\n"
        b"147\n"
        b"%%EOF"
    )


# ------------------------------------------------------------------ #
# Test — Upload (CREATE)
# ------------------------------------------------------------------ #

@pytest.mark.asyncio
async def test_upload_pdf_success(async_client: AsyncClient, fake_pdf_bytes: bytes):
    """
    Dado: un PDF válido con nombre personalizado
    Cuando: se envía POST /api/v1/documents/
    Entonces:
      - Status code 201 Created
      - La respuesta contiene id, name, checksum, extracted_text
      - El documento existe en MongoDB
      - El checksum es SHA-256 válido (64 chars hex)
      - El name coincide con el custom_name enviado
    """
    # Arrange
    custom_name = "Mi Documento de Prueba"
    files = {"file": ("original.pdf", fake_pdf_bytes, "application/pdf")}
    data = {"custom_name": custom_name}

    # Act
    response = await async_client.post(
        "/api/v1/documents/",
        files=files,
        data=data,
    )

    # Assert — HTTP
    assert response.status_code == 201, f"Expected 201, got {response.status_code}: {response.text}"

    body = response.json()
    assert "id" in body
    assert body["name"] == custom_name
    assert len(body["checksum"]) == 64  # SHA-256 hex
    assert isinstance(body["extracted_text"], str)
    assert "created_at" in body
    assert "updated_at" in body
    # Nuevo: la respuesta debe incluir un preview de texto (primeros 500 chars)
    assert "text_preview" in body
    assert body["text_preview"] == body["extracted_text"][:500]

    # Assert — Persistencia en MongoDB
    doc_id = body["id"]
    doc_in_db = await DocumentModel.get(doc_id)
    assert doc_in_db is not None, "El documento no fue encontrado en MongoDB"
    assert doc_in_db.name == custom_name
    assert doc_in_db.checksum == body["checksum"]


@pytest.mark.asyncio
async def test_upload_pdf_without_custom_name_uses_filename(async_client: AsyncClient, fake_pdf_bytes: bytes):
    """
    Dado: un PDF válido SIN custom_name
    Cuando: se envía POST /api/v1/documents/
    Entonces: el name de la respuesta usa el filename original del archivo.
    """
    original_filename = "contrato_2024.pdf"
    files = {"file": (original_filename, fake_pdf_bytes, "application/pdf")}

    response = await async_client.post(
        "/api/v1/documents/",
        files=files,
    )

    assert response.status_code == 201
    body = response.json()
    assert body["name"] == original_filename
    assert "text_preview" in body


@pytest.mark.asyncio
async def test_upload_duplicate_pdf_returns_409(async_client: AsyncClient, fake_pdf_bytes: bytes):
    """
    Dado: un PDF ya subido anteriormente (mismo contenido = mismo checksum)
    Cuando: se intenta subir de nuevo
    Entonces: debe retornar 409 Conflict
    """
    files = {"file": ("doc1.pdf", fake_pdf_bytes, "application/pdf")}

    # Primera subida — éxito
    response1 = await async_client.post("/api/v1/documents/", files=files)
    assert response1.status_code == 201

    # Segunda subida — mismo contenido, diferente nombre
    files2 = {"file": ("doc2.pdf", fake_pdf_bytes, "application/pdf")}
    response2 = await async_client.post("/api/v1/documents/", files=files2)

    assert response2.status_code == 409
    # ProblemDetail format
    body = response2.json()
    assert set(["type", "title", "status", "detail", "instance"]).issubset(set(body.keys()))
    assert body["status"] == 409


@pytest.mark.asyncio
async def test_upload_non_pdf_returns_400(async_client: AsyncClient):
    """
    Dado: un archivo que NO es PDF (magic bytes inválidos)
    Cuando: se envía POST /api/v1/documents/
    Entonces: debe retornar 400 Bad Request
    """
    fake_docx = b"PK\x03\x04 this is a word document"
    files = {"file": ("documento.docx", fake_docx, "application/pdf")}

    response = await async_client.post(
        "/api/v1/documents/",
        files=files,
    )

    assert response.status_code == 400
    body = response.json()
    # ProblemDetail format expected
    assert set(["type", "title", "status", "detail", "instance"]).issubset(set(body.keys()))
    assert body["status"] == 400
    assert "no es un PDF válido" in body["detail"]