"""
test_find_pdf.py — Test de integración para las operaciones READ (buscar documentos)
=====================================================================================
Este test verifica el flujo completo de búsqueda de documentos:
  - GET /api/v1/documents/           → listar todos los documentos
  - GET /api/v1/documents/{id}       → obtener un documento por ID

Casos cubiertos:
  1. Listar cuando la colección está vacía → lista vacía, no error.
  2. Listar con un documento → aparece en la respuesta con todos sus campos.
  3. Listar con múltiples documentos → aparecen todos.
  4. Buscar por ID existente → 200 con los datos correctos.
  5. Buscar por ID inexistente → 404.
  6. Buscar por ID con formato inválido → 404.
  7. Los campos de la respuesta tienen el formato correcto (checksum hex, timestamps).
  8. El documento encontrado por ID coincide con el subido originalmente.

Estrategia de integración:
  - Usamos MongoDB real (ya corriendo localmente).
  - Usamos httpx.AsyncClient con ASGITransport para hacer requests HTTP a la app FastAPI.
  - Limpiamos la colección "documents" antes y después de cada test para aislamiento.
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
# Tests — GET /api/v1/documents/ (listar todos)
# ------------------------------------------------------------------ #

@pytest.mark.asyncio
async def test_get_all_empty_collection_returns_empty_list(async_client: AsyncClient):
    """
    Dado: la colección de documentos está vacía
    Cuando: se envía GET /api/v1/documents/
    Entonces:
      - Status code 200 OK
      - La respuesta es una lista vacía (no null, no error)
    """
    response = await async_client.get("/api/v1/documents/")

    assert response.status_code == 200, (
        f"Expected 200, got {response.status_code}: {response.text}"
    )
    body = response.json()
    assert isinstance(body, list)
    assert len(body) == 0


@pytest.mark.asyncio
async def test_get_all_returns_one_document_after_upload(async_client: AsyncClient, fake_pdf_bytes: bytes):
    """
    Dado: un documento subido
    Cuando: se envía GET /api/v1/documents/
    Entonces:
      - Status code 200 OK
      - La lista contiene exactamente un elemento
      - El elemento tiene todos los campos esperados: id, name, checksum, extracted_text, created_at, updated_at
    """
    # Arrange — subir un documento
    files = {"file": ("informe.pdf", fake_pdf_bytes, "application/pdf")}
    data = {"custom_name": "Informe Anual"}
    upload = await async_client.post("/api/v1/documents/", files=files, data=data)
    assert upload.status_code == 201

    # Act
    response = await async_client.get("/api/v1/documents/")

    # Assert
    assert response.status_code == 200
    body = response.json()
    assert isinstance(body, list)
    assert len(body) == 1

    doc = body[0]
    assert "id" in doc
    assert doc["name"] == "Informe Anual"
    assert "checksum" in doc
    assert "extracted_text" in doc
    assert "created_at" in doc
    assert "updated_at" in doc


@pytest.mark.asyncio
async def test_get_all_returns_all_uploaded_documents(async_client: AsyncClient, fake_pdf_bytes: bytes):
    """
    Dado: tres documentos subidos con contenidos distintos
    Cuando: se envía GET /api/v1/documents/
    Entonces:
      - Status code 200 OK
      - La lista contiene exactamente tres elementos
      - Los tres IDs están presentes en la respuesta
    """
    # Arrange — tres PDFs con contenido diferente (checksums distintos)
    pdf_a = fake_pdf_bytes
    pdf_b = fake_pdf_bytes[:-1] + b"B"
    pdf_c = fake_pdf_bytes[:-1] + b"C"

    uploaded_ids = []
    for i, pdf in enumerate([pdf_a, pdf_b, pdf_c], start=1):
        files = {"file": (f"doc_{i}.pdf", pdf, "application/pdf")}
        resp = await async_client.post("/api/v1/documents/", files=files)
        assert resp.status_code == 201, f"Upload {i} falló: {resp.text}"
        uploaded_ids.append(resp.json()["id"])

    # Act
    response = await async_client.get("/api/v1/documents/")

    # Assert
    assert response.status_code == 200
    body = response.json()
    assert len(body) == 3

    response_ids = {doc["id"] for doc in body}
    for uid in uploaded_ids:
        assert uid in response_ids, f"ID {uid} no encontrado en la lista"


@pytest.mark.asyncio
async def test_get_all_uses_custom_name_as_name_field(async_client: AsyncClient, fake_pdf_bytes: bytes):
    """
    Dado: un documento subido con custom_name
    Cuando: se consulta GET /api/v1/documents/
    Entonces: el campo 'name' del documento es el custom_name enviado, no el filename original
    """
    custom = "Mi Reporte Q4"
    files = {"file": ("archivo_original.pdf", fake_pdf_bytes, "application/pdf")}
    data = {"custom_name": custom}
    await async_client.post("/api/v1/documents/", files=files, data=data)

    response = await async_client.get("/api/v1/documents/")
    assert response.status_code == 200

    doc = response.json()[0]
    assert doc["name"] == custom


@pytest.mark.asyncio
async def test_get_all_uses_filename_when_no_custom_name(async_client: AsyncClient, fake_pdf_bytes: bytes):
    """
    Dado: un documento subido SIN custom_name
    Cuando: se consulta GET /api/v1/documents/
    Entonces: el campo 'name' es el nombre original del archivo
    """
    original_filename = "contrato_2025.pdf"
    files = {"file": (original_filename, fake_pdf_bytes, "application/pdf")}
    await async_client.post("/api/v1/documents/", files=files)

    response = await async_client.get("/api/v1/documents/")
    assert response.status_code == 200

    doc = response.json()[0]
    assert doc["name"] == original_filename


# ------------------------------------------------------------------ #
# Tests — GET /api/v1/documents/{id} (buscar por ID)
# ------------------------------------------------------------------ #

@pytest.mark.asyncio
async def test_get_by_id_returns_correct_document(async_client: AsyncClient, fake_pdf_bytes: bytes):
    """
    Dado: un documento existente con ID conocido
    Cuando: se envía GET /api/v1/documents/{id}
    Entonces:
      - Status code 200 OK
      - La respuesta contiene el documento con los datos correctos
      - El ID de la respuesta coincide con el solicitado
    """
    # Arrange — subir documento y capturar su ID
    custom_name = "Acta de Reunión"
    files = {"file": ("acta.pdf", fake_pdf_bytes, "application/pdf")}
    data = {"custom_name": custom_name}
    upload = await async_client.post("/api/v1/documents/", files=files, data=data)
    assert upload.status_code == 201
    doc_id = upload.json()["id"]

    # Act
    response = await async_client.get(f"/api/v1/documents/{doc_id}")

    # Assert
    assert response.status_code == 200, (
        f"Expected 200, got {response.status_code}: {response.text}"
    )
    body = response.json()
    assert body["id"] == doc_id
    assert body["name"] == custom_name
    assert "checksum" in body
    assert "extracted_text" in body
    assert "created_at" in body
    assert "updated_at" in body


@pytest.mark.asyncio
async def test_get_by_id_data_matches_upload_response(async_client: AsyncClient, fake_pdf_bytes: bytes):
    """
    Dado: un documento subido correctamente
    Cuando: se busca por su ID
    Entonces: todos los campos de la respuesta coinciden con los del upload original
    """
    # Arrange
    files = {"file": ("balance.pdf", fake_pdf_bytes, "application/pdf")}
    upload = await async_client.post("/api/v1/documents/", files=files)
    assert upload.status_code == 201
    upload_body = upload.json()
    doc_id = upload_body["id"]

    # Act
    response = await async_client.get(f"/api/v1/documents/{doc_id}")

    # Assert — todos los campos deben coincidir con lo que devolvió el upload
    assert response.status_code == 200
    get_body = response.json()

    assert get_body["id"] == upload_body["id"]
    assert get_body["name"] == upload_body["name"]
    assert get_body["checksum"] == upload_body["checksum"]
    assert get_body["extracted_text"] == upload_body["extracted_text"]


@pytest.mark.asyncio
async def test_get_by_id_checksum_is_valid_sha256(async_client: AsyncClient, fake_pdf_bytes: bytes):
    """
    Dado: un documento subido
    Cuando: se busca por su ID
    Entonces: el campo checksum es un SHA-256 válido (64 caracteres hexadecimales)
    """
    files = {"file": ("tecnico.pdf", fake_pdf_bytes, "application/pdf")}
    upload = await async_client.post("/api/v1/documents/", files=files)
    assert upload.status_code == 201
    doc_id = upload.json()["id"]

    response = await async_client.get(f"/api/v1/documents/{doc_id}")
    assert response.status_code == 200

    checksum = response.json()["checksum"]
    assert len(checksum) == 64, f"SHA-256 debe tener 64 chars, tiene {len(checksum)}"
    assert all(c in "0123456789abcdef" for c in checksum.lower()), (
        f"Checksum contiene caracteres no hexadecimales: {checksum}"
    )


@pytest.mark.asyncio
async def test_get_by_id_nonexistent_returns_404(async_client: AsyncClient):
    """
    Dado: un ID válido en formato pero que no existe en la base de datos
    Cuando: se envía GET /api/v1/documents/{id}
    Entonces: debe retornar 404 Not Found con detalle descriptivo
    """
    nonexistent_id = "000000000000000000000001"

    response = await async_client.get(f"/api/v1/documents/{nonexistent_id}")

    assert response.status_code == 404
    body = response.json()
    assert "detail" in body
    assert nonexistent_id in body["detail"]


@pytest.mark.asyncio
async def test_get_by_id_invalid_format_returns_404(async_client: AsyncClient):
    """
    Dado: un ID con formato inválido (no es un ObjectId de MongoDB)
    Cuando: se envía GET /api/v1/documents/{id}
    Entonces: debe retornar 404 Not Found
    (el repositorio retorna None al no poder parsear el ObjectId)
    """
    invalid_id = "esto-no-es-un-id-valido"

    response = await async_client.get(f"/api/v1/documents/{invalid_id}")

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_by_id_returns_correct_doc_among_many(async_client: AsyncClient, fake_pdf_bytes: bytes):
    """
    Dado: varios documentos subidos
    Cuando: se busca por el ID de uno específico
    Entonces: se retorna ese documento y no otro
    """
    # Arrange — subir tres PDFs distintos
    pdf_a = fake_pdf_bytes
    pdf_b = fake_pdf_bytes[:-1] + b"B"
    pdf_c = fake_pdf_bytes[:-1] + b"C"

    ids = {}
    for nombre, pdf in [("alfa.pdf", pdf_a), ("beta.pdf", pdf_b), ("gamma.pdf", pdf_c)]:
        files = {"file": (nombre, pdf, "application/pdf")}
        data = {"custom_name": nombre}
        resp = await async_client.post("/api/v1/documents/", files=files, data=data)
        assert resp.status_code == 201
        ids[nombre] = resp.json()["id"]

    # Act — buscar específicamente el segundo
    target_id = ids["beta.pdf"]
    response = await async_client.get(f"/api/v1/documents/{target_id}")

    # Assert
    assert response.status_code == 200
    body = response.json()
    assert body["id"] == target_id
    assert body["name"] == "beta.pdf"


@pytest.mark.asyncio
async def test_get_by_id_extracted_text_is_string(async_client: AsyncClient, fake_pdf_bytes: bytes):
    """
    Dado: un documento subido (PDF sin texto real, ya que es un fake)
    Cuando: se busca por su ID
    Entonces: el campo extracted_text es un string (vacío o no, nunca None)
    """
    files = {"file": ("vacio.pdf", fake_pdf_bytes, "application/pdf")}
    upload = await async_client.post("/api/v1/documents/", files=files)
    assert upload.status_code == 201
    doc_id = upload.json()["id"]

    response = await async_client.get(f"/api/v1/documents/{doc_id}")
    assert response.status_code == 200

    extracted = response.json()["extracted_text"]
    assert isinstance(extracted, str), f"extracted_text debería ser str, es {type(extracted)}"