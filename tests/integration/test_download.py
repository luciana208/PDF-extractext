import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from beanie import init_beanie

from app.main import app
from app.data.database.mongo_connection import connect, disconnect, get_database
from app.data.models.document_model import DocumentModel


@pytest_asyncio.fixture(scope="function")
async def clean_database():
    await connect()
    db = get_database()
    await init_beanie(database=db, document_models=[DocumentModel])
    await DocumentModel.delete_all()
    yield db
    await DocumentModel.delete_all()
    await disconnect()


@pytest_asyncio.fixture(scope="function")
async def async_client(clean_database):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


@pytest.fixture
def fake_pdf_bytes() -> bytes:
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


@pytest.mark.asyncio
async def test_download_text_file(async_client: AsyncClient, fake_pdf_bytes: bytes):
    original_filename = "contrato_para_descarga.pdf"
    files = {"file": (original_filename, fake_pdf_bytes, "application/pdf")}

    # Upload
    response = await async_client.post("/api/v1/documents/", files=files)
    assert response.status_code == 201
    body = response.json()
    doc_id = body["id"]

    # Download
    download_resp = await async_client.get(f"/api/v1/documents/{doc_id}/download")
    assert download_resp.status_code == 200

    # Content-Disposition filename should be original name with .txt extension
    disposition = download_resp.headers.get("content-disposition", "")
    assert "attachment" in disposition
    assert "contrato_para_descarga.txt" in disposition

    # Body should equal the extracted_text stored
    assert download_resp.text == body["extracted_text"]
