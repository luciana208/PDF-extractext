"""
test_extraction.py — Test de integracion para la extraccion de texto
====================================================================
Este test verifica que el sistema extrae correctamente el texto de los PDFs.
"""

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from beanie import init_beanie

from app.main import app
from app.data.database.mongo_connection import connect, disconnect, get_database
from app.data.models.document_model import DocumentModel


@pytest_asyncio.fixture(scope="function")
async def clean_database():
    """Conecta a MongoDB, inicializa Beanie, limpia la coleccion."""
    await connect()
    db = get_database()
    await init_beanie(database=db, document_models=[DocumentModel])
    await DocumentModel.delete_all()
    yield db
    await DocumentModel.delete_all()
    await disconnect()


@pytest_asyncio.fixture(scope="function")
async def async_client(clean_database):
    """Cliente HTTP async para requests a la app FastAPI."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


def _make_pdf(lines: list[str]) -> bytes:
    """Construye bytes de PDF uniendo lineas con newline."""
    return "\n".join(lines).encode("ascii")


@pytest.fixture
def pdf_with_text() -> bytes:
    """PDF minimo con texto seleccionable."""
    return _make_pdf([
        "%PDF-1.4",
        "1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj",
        "2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj",
        "3 0 obj<</Type/Page/MediaBox[0 0 612 792]/Contents 4 0 R/Resources<</Font<</F1 5 0 R>>>>>>endobj",
        "4 0 obj<</Length 52>>stream",
        "BT /F1 12 Tf 100 700 Td (Hola Mundo PDF) Tj ET",
        "endstream endobj",
        "5 0 obj<</Type/Font/Subtype/Type1/BaseFont/Helvetica>>endobj",
        "xref",
        "0 6",
        "0000000000 65535 f",
        "0000000009 00000 n",
        "0000000052 00000 n",
        "0000000101 00000 n",
        "0000000212 00000 n",
        "0000000314 00000 n",
        "trailer<</Size 6/Root 1 0 R>>",
        "startxref",
        "380",
        "%%EOF",
    ])


@pytest.fixture
def pdf_without_text() -> bytes:
    """PDF sin texto seleccionable."""
    return _make_pdf([
        "%PDF-1.4",
        "1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj",
        "2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj",
        "3 0 obj<</Type/Page/MediaBox[0 0 612 792]>>endobj",
        "xref",
        "0 4",
        "0000000000 65535 f",
        "0000000009 00000 n",
        "0000000052 00000 n",
        "0000000101 00000 n",
        "trailer<</Size 4/Root 1 0 R>>",
        "startxref",
        "147",
        "%%EOF",
    ])


@pytest.mark.asyncio
async def test_extracts_text_from_pdf_with_content(async_client: AsyncClient, pdf_with_text: bytes):
    """
    Dado: un PDF con texto seleccionable
    Cuando: se sube via POST
    Entonces: extracted_text contiene el texto y se persiste en MongoDB.
    """
    files = {"file": ("documento_con_texto.pdf", pdf_with_text, "application/pdf")}
    data = {"custom_name": "Doc con texto"}

    response = await async_client.post("/api/v1/documents/", files=files, data=data)

    assert response.status_code == 201, f"Error: {response.text}"
    body = response.json()

    assert "Hola Mundo PDF" in body["extracted_text"], f"Texto no extraido: {body['extracted_text']!r}"
    assert len(body["extracted_text"]) > 0

    doc_in_db = await DocumentModel.get(body["id"])
    assert doc_in_db is not None
    assert "Hola Mundo PDF" in doc_in_db.extracted_text


@pytest.mark.asyncio
async def test_returns_empty_text_for_scanned_pdf(async_client: AsyncClient, pdf_without_text: bytes):
    """
    Dado: un PDF sin texto
    Cuando: se sube via POST
    Entonces: extracted_text es vacio.
    """
    files = {"file": ("escaneado.pdf", pdf_without_text, "application/pdf")}
    data = {"custom_name": "PDF escaneado"}

    response = await async_client.post("/api/v1/documents/", files=files, data=data)

    assert response.status_code == 201
    body = response.json()

    assert body["extracted_text"] == "", f"Esperado '', got: {body['extracted_text']!r}"

    doc_in_db = await DocumentModel.get(body["id"])
    assert doc_in_db is not None
    assert doc_in_db.extracted_text == ""


@pytest.mark.asyncio
async def test_checksum_is_sha256(async_client: AsyncClient, pdf_with_text: bytes):
    """Verifica que el checksum es SHA-256 valido."""
    files = {"file": ("test.pdf", pdf_with_text, "application/pdf")}

    response = await async_client.post("/api/v1/documents/", files=files)

    assert response.status_code == 201
    body = response.json()

    checksum = body["checksum"]
    assert len(checksum) == 64
    assert all(c in "0123456789abcdef" for c in checksum.lower())

    response2 = await async_client.post("/api/v1/documents/", files=files)
    assert response2.status_code == 409