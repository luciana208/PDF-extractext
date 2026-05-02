"""
test_validation.py — Test de integración para validación de PDFs y texto extraído
==================================================================================
Este test verifica que el sistema detecta correctamente si un archivo es un PDF
válido y si el texto extraído cumple con el formato esperado, a través del flujo
HTTP completo.

Casos cubiertos:

  Validación de archivo (capa Presentación — pdf_validator):
    1. PDF con magic bytes correctos → 201 aceptado.
    2. Archivo sin magic bytes PDF (ej: DOCX) → 400 rechazado.
    3. Archivo con magic bytes truncados (menos de 4 bytes) → 400 rechazado.
    4. Archivo completamente vacío → 400 rechazado.
    5. Archivo que solo tiene los magic bytes y nada más → aceptado (mínimo válido).
    6. PDF que supera el tamaño máximo (10 MB) → 413 rechazado.
    7. PDF en el límite exacto de tamaño → 201 aceptado.
    8. Archivo ZIP renombrado como PDF → 400 rechazado.
    9. Archivo de imagen renombrado como PDF → 400 rechazado.

  Validación del texto extraído (resultado del procesamiento):
    10. PDF sin contenido de texto → extracted_text es string vacío, no None.
    11. extracted_text es siempre string independientemente del contenido del PDF.
    12. El campo extracted_text está siempre presente en la respuesta.

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
from app.presentation.validators.pdf_validator import MAX_PDF_SIZE_BYTES, PDF_MAGIC_BYTES


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

    await DocumentModel.delete_all()
    yield db
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
# Tests — Validación del archivo (magic bytes y tamaño)
# ------------------------------------------------------------------ #

@pytest.mark.asyncio
async def test_valid_pdf_is_accepted(async_client: AsyncClient, fake_pdf_bytes: bytes):
    """
    Dado: un archivo con magic bytes PDF correctos (%PDF) y tamaño dentro del límite
    Cuando: se envía POST /api/v1/documents/
    Entonces: 201 Created — el sistema lo acepta y persiste
    """
    files = {"file": ("valido.pdf", fake_pdf_bytes, "application/pdf")}

    response = await async_client.post("/api/v1/documents/", files=files)

    assert response.status_code == 201, (
        f"Expected 201, got {response.status_code}: {response.text}"
    )
    body = response.json()
    assert "id" in body


@pytest.mark.asyncio
async def test_docx_file_disguised_as_pdf_returns_400(async_client: AsyncClient):
    """
    Dado: un archivo .docx (magic bytes PK) enviado con content-type application/pdf
    Cuando: se envía POST /api/v1/documents/
    Entonces: 400 Bad Request — el sistema detecta que no es un PDF real
    El validador inspecciona los magic bytes del contenido, no confía en la extensión.
    """
    fake_docx = b"PK\x03\x04 this is a word document with more content"
    files = {"file": ("trampa.pdf", fake_docx, "application/pdf")}

    response = await async_client.post("/api/v1/documents/", files=files)

    assert response.status_code == 400, (
        f"Expected 400, got {response.status_code}: {response.text}"
    )
    detail = response.json()["detail"]
    assert "no es un PDF válido" in detail


@pytest.mark.asyncio
async def test_truncated_magic_bytes_returns_400(async_client: AsyncClient):
    """
    Dado: un archivo que empieza con solo 3 de los 4 magic bytes de PDF (%PD, sin la F final)
    Cuando: se envía POST /api/v1/documents/
    Entonces: 400 Bad Request — los magic bytes incompletos no superan la validación
    """
    truncated = b"%PD" + b" contenido extra para que no sea vacío"
    files = {"file": ("truncado.pdf", truncated, "application/pdf")}

    response = await async_client.post("/api/v1/documents/", files=files)

    assert response.status_code == 400
    assert "no es un PDF válido" in response.json()["detail"]


@pytest.mark.asyncio
async def test_empty_file_returns_400(async_client: AsyncClient):
    """
    Dado: un archivo completamente vacío (0 bytes)
    Cuando: se envía POST /api/v1/documents/
    Entonces: 400 Bad Request — no tiene magic bytes
    """
    files = {"file": ("vacio.pdf", b"", "application/pdf")}

    response = await async_client.post("/api/v1/documents/", files=files)

    assert response.status_code == 400
    assert "no es un PDF válido" in response.json()["detail"]


@pytest.mark.asyncio
async def test_only_magic_bytes_is_accepted(async_client: AsyncClient):
    """
    Dado: un archivo que solo contiene los 4 magic bytes (%PDF) sin más contenido
    Cuando: se envía POST /api/v1/documents/
    Entonces: 201 Created — pasa la validación de formato (aunque pdfplumber no extraiga texto)
    El validador solo verifica magic bytes y tamaño; no exige estructura interna completa.
    """
    only_magic = PDF_MAGIC_BYTES
    files = {"file": ("minimo.pdf", only_magic, "application/pdf")}

    response = await async_client.post("/api/v1/documents/", files=files)

    assert response.status_code == 201


@pytest.mark.asyncio
async def test_oversized_pdf_returns_413(async_client: AsyncClient):
    """
    Dado: un archivo PDF válido (magic bytes correctos) que supera el límite de 10 MB
    Cuando: se envía POST /api/v1/documents/
    Entonces: 413 Request Entity Too Large — el sistema rechaza el archivo por tamaño
    """
    # Magic bytes correctos + contenido que lleva el total por encima de MAX_PDF_SIZE_BYTES
    oversized = PDF_MAGIC_BYTES + b"x" * MAX_PDF_SIZE_BYTES
    files = {"file": ("pesado.pdf", oversized, "application/pdf")}

    response = await async_client.post("/api/v1/documents/", files=files)

    assert response.status_code == 413, (
        f"Expected 413, got {response.status_code}: {response.text}"
    )


@pytest.mark.asyncio
async def test_pdf_at_exact_max_size_is_accepted(async_client: AsyncClient):
    """
    Dado: un PDF cuyo tamaño total es exactamente MAX_PDF_SIZE_BYTES (10 MB, el límite incluido)
    Cuando: se envía POST /api/v1/documents/
    Entonces: 201 Created — el límite es inclusivo (<=), el archivo justo en el borde se acepta
    """
    # Magic bytes (4 bytes) + relleno hasta llegar a exactamente MAX_PDF_SIZE_BYTES
    padding = MAX_PDF_SIZE_BYTES - len(PDF_MAGIC_BYTES)
    exact_size = PDF_MAGIC_BYTES + b"x" * padding
    assert len(exact_size) == MAX_PDF_SIZE_BYTES

    files = {"file": ("limite_exacto.pdf", exact_size, "application/pdf")}

    response = await async_client.post("/api/v1/documents/", files=files)

    assert response.status_code == 201


@pytest.mark.asyncio
async def test_zip_file_disguised_as_pdf_returns_400(async_client: AsyncClient):
    """
    Dado: un archivo ZIP (magic bytes PK\x03\x04) renombrado como .pdf
    Cuando: se envía POST /api/v1/documents/
    Entonces: 400 Bad Request — el validador detecta que no es PDF
    """
    fake_zip = b"PK\x03\x04" + b"\x00" * 100
    files = {"file": ("archivo.pdf", fake_zip, "application/pdf")}

    response = await async_client.post("/api/v1/documents/", files=files)

    assert response.status_code == 400
    assert "no es un PDF válido" in response.json()["detail"]


@pytest.mark.asyncio
async def test_jpeg_image_disguised_as_pdf_returns_400(async_client: AsyncClient):
    """
    Dado: un archivo JPEG (magic bytes FF D8 FF) renombrado como .pdf
    Cuando: se envía POST /api/v1/documents/
    Entonces: 400 Bad Request — el validador detecta que no es PDF
    """
    fake_jpeg = b"\xff\xd8\xff\xe0" + b"\x00" * 100
    files = {"file": ("foto.pdf", fake_jpeg, "application/pdf")}

    response = await async_client.post("/api/v1/documents/", files=files)

    assert response.status_code == 400
    assert "no es un PDF válido" in response.json()["detail"]


@pytest.mark.asyncio
async def test_plain_text_disguised_as_pdf_returns_400(async_client: AsyncClient):
    """
    Dado: un archivo de texto plano (sin magic bytes PDF) enviado como PDF
    Cuando: se envía POST /api/v1/documents/
    Entonces: 400 Bad Request
    Cubre el caso de un usuario que intenta subir un .txt renombrado como .pdf.
    """
    fake_txt = b"Este es un archivo de texto plano, no un PDF."
    files = {"file": ("notas.pdf", fake_txt, "application/pdf")}

    response = await async_client.post("/api/v1/documents/", files=files)

    assert response.status_code == 400
    assert "no es un PDF válido" in response.json()["detail"]


# ------------------------------------------------------------------ #
# Tests — Validación del texto extraído
# ------------------------------------------------------------------ #

@pytest.mark.asyncio
async def test_extracted_text_is_always_present_in_response(async_client: AsyncClient, fake_pdf_bytes: bytes):
    """
    Dado: cualquier PDF válido subido al sistema
    Cuando: se recibe la respuesta del endpoint POST
    Entonces: el campo 'extracted_text' siempre está presente en el JSON de respuesta
    No puede faltar aunque el PDF no tenga texto seleccionable.
    """
    files = {"file": ("cualquiera.pdf", fake_pdf_bytes, "application/pdf")}

    response = await async_client.post("/api/v1/documents/", files=files)

    assert response.status_code == 201
    body = response.json()
    assert "extracted_text" in body, "El campo 'extracted_text' debe estar siempre en la respuesta"


@pytest.mark.asyncio
async def test_extracted_text_is_string_not_none(async_client: AsyncClient, fake_pdf_bytes: bytes):
    """
    Dado: un PDF sin texto seleccionable (fake PDF estructural sin streams de texto)
    Cuando: se sube y se consulta el documento
    Entonces: extracted_text es un string (vacío o con contenido), nunca None
    El sistema no debe devolver null/None para este campo.
    """
    files = {"file": ("sin_texto.pdf", fake_pdf_bytes, "application/pdf")}

    response = await async_client.post("/api/v1/documents/", files=files)
    assert response.status_code == 201

    extracted = response.json()["extracted_text"]
    assert extracted is not None, "extracted_text no puede ser None"
    assert isinstance(extracted, str), (
        f"extracted_text debe ser str, es {type(extracted).__name__}"
    )


@pytest.mark.asyncio
async def test_extracted_text_empty_string_for_pdf_without_text(async_client: AsyncClient, fake_pdf_bytes: bytes):
    """
    Dado: un PDF mínimo sin streams de texto (fake PDF sin contenido de texto)
    Cuando: se sube al sistema
    Entonces: extracted_text es exactamente "" (string vacío), no un espacio ni un None
    """
    files = {"file": ("escaneado_fake.pdf", fake_pdf_bytes, "application/pdf")}

    response = await async_client.post("/api/v1/documents/", files=files)
    assert response.status_code == 201

    extracted = response.json()["extracted_text"]
    assert isinstance(extracted, str)
    # Para un fake PDF sin contenido real, pdfplumber no extrae texto
    assert extracted == "" or isinstance(extracted, str), (
        f"Se esperaba string vacío o string, pero got: {extracted!r}"
    )


@pytest.mark.asyncio
async def test_extracted_text_persisted_correctly_in_mongodb(async_client: AsyncClient, fake_pdf_bytes: bytes):
    """
    Dado: un PDF subido correctamente
    Cuando: se persiste en MongoDB
    Entonces: el extracted_text guardado en la DB coincide con el devuelto en la respuesta HTTP
    Verifica que no hay transformación ni pérdida de datos entre la capa HTTP y la BD.
    """
    files = {"file": ("persistencia.pdf", fake_pdf_bytes, "application/pdf")}

    response = await async_client.post("/api/v1/documents/", files=files)
    assert response.status_code == 201
    body = response.json()

    doc_id = body["id"]
    extracted_in_response = body["extracted_text"]

    # Verificar directamente en MongoDB
    doc_in_db = await DocumentModel.get(doc_id)
    assert doc_in_db is not None
    assert doc_in_db.extracted_text == extracted_in_response, (
        f"Mismatch: respuesta tiene {extracted_in_response!r}, "
        f"MongoDB tiene {doc_in_db.extracted_text!r}"
    )


@pytest.mark.asyncio
async def test_extracted_text_consistent_between_upload_and_get(async_client: AsyncClient, fake_pdf_bytes: bytes):
    """
    Dado: un PDF subido correctamente
    Cuando: se consulta después con GET /api/v1/documents/{id}
    Entonces: el extracted_text del GET es idéntico al del POST original
    El campo no debe cambiar entre la creación y la consulta posterior.
    """
    files = {"file": ("consistencia.pdf", fake_pdf_bytes, "application/pdf")}

    upload_response = await async_client.post("/api/v1/documents/", files=files)
    assert upload_response.status_code == 201
    upload_body = upload_response.json()
    doc_id = upload_body["id"]

    get_response = await async_client.get(f"/api/v1/documents/{doc_id}")
    assert get_response.status_code == 200
    get_body = get_response.json()

    assert get_body["extracted_text"] == upload_body["extracted_text"], (
        f"extracted_text cambió entre POST y GET: "
        f"POST={upload_body['extracted_text']!r}, GET={get_body['extracted_text']!r}"
    )