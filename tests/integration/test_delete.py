"""
test_delete.py — Test de integración para la operación DELETE (eliminar documento)
==================================================================================
Este test verifica el flujo completo de eliminación de un documento:
  1. Subir un PDF válido para tener un documento en la DB.
  2. Enviar DELETE /api/v1/documents/{id}.
  3. Verificar que la respuesta es 200 OK con el mensaje esperado.
  4. Verificar que el documento ya no existe en MongoDB.
  5. Verificar que intentar eliminar el mismo ID devuelve 404.
  6. Verificar que un ID con formato inválido devuelve 404.

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
# Tests — Delete
# ------------------------------------------------------------------ #

@pytest.mark.asyncio
async def test_delete_document_success(async_client: AsyncClient, fake_pdf_bytes: bytes):
    """
    Dado: un documento existente en la base de datos
    Cuando: se envía DELETE /api/v1/documents/{id}
    Entonces:
      - Status code 200 OK
      - La respuesta contiene un mensaje de confirmación con el ID
      - El documento ya NO existe en MongoDB
    """
    # Arrange — subir un documento primero
    files = {"file": ("a_borrar.pdf", fake_pdf_bytes, "application/pdf")}
    upload_response = await async_client.post("/api/v1/documents/", files=files)
    assert upload_response.status_code == 201, (
        f"Setup falló: expected 201, got {upload_response.status_code}: {upload_response.text}"
    )
    doc_id = upload_response.json()["id"]

    # Act
    response = await async_client.delete(f"/api/v1/documents/{doc_id}")

    # Assert — HTTP
    assert response.status_code == 200, (
        f"Expected 200, got {response.status_code}: {response.text}"
    )
    body = response.json()
    assert "message" in body
    assert doc_id in body["message"]

    # Assert — El documento ya no existe en MongoDB
    doc_in_db = await DocumentModel.get(doc_id)
    assert doc_in_db is None, f"El documento {doc_id} debería haber sido eliminado de MongoDB"


@pytest.mark.asyncio
async def test_delete_nonexistent_document_returns_404(async_client: AsyncClient):
    """
    Dado: un ID de documento que no existe en la base de datos
    Cuando: se envía DELETE /api/v1/documents/{id}
    Entonces: debe retornar 404 Not Found
    """
    # ObjectId válido en formato pero que no existe en la DB
    nonexistent_id = "000000000000000000000001"

    response = await async_client.delete(f"/api/v1/documents/{nonexistent_id}")

    assert response.status_code == 404
    body = response.json()
    assert "detail" in body
    assert nonexistent_id in body["detail"]


@pytest.mark.asyncio
async def test_delete_already_deleted_document_returns_404(async_client: AsyncClient, fake_pdf_bytes: bytes):
    """
    Dado: un documento que ya fue eliminado
    Cuando: se intenta eliminar de nuevo con el mismo ID
    Entonces: debe retornar 404 Not Found en el segundo intento
    """
    # Arrange — subir y luego eliminar
    files = {"file": ("efimero.pdf", fake_pdf_bytes, "application/pdf")}
    upload_response = await async_client.post("/api/v1/documents/", files=files)
    assert upload_response.status_code == 201
    doc_id = upload_response.json()["id"]

    # Primera eliminación — éxito
    first_delete = await async_client.delete(f"/api/v1/documents/{doc_id}")
    assert first_delete.status_code == 200

    # Segunda eliminación — debe fallar con 404
    second_delete = await async_client.delete(f"/api/v1/documents/{doc_id}")

    assert second_delete.status_code == 404
    assert doc_id in second_delete.json()["detail"]


@pytest.mark.asyncio
async def test_delete_invalid_id_format_returns_404(async_client: AsyncClient):
    """
    Dado: un ID con formato inválido (no es un ObjectId de MongoDB)
    Cuando: se envía DELETE /api/v1/documents/{id}
    Entonces: debe retornar 404 Not Found
    (el repositorio retorna False al no poder parsear el ObjectId,
    el servicio lanza DocumentNotFoundError, el controller devuelve 404)
    """
    invalid_id = "esto-no-es-un-object-id"

    response = await async_client.delete(f"/api/v1/documents/{invalid_id}")

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_document_not_in_get_all_after_deletion(async_client: AsyncClient, fake_pdf_bytes: bytes):
    """
    Dado: dos documentos subidos, luego se elimina uno
    Cuando: se consulta GET /api/v1/documents/
    Entonces:
      - Solo aparece el documento que NO fue eliminado
      - La lista tiene exactamente 1 elemento
    """
    # Arrange — subir dos PDFs distintos
    pdf_1 = fake_pdf_bytes
    pdf_2 = fake_pdf_bytes[:-1] + b"X"  # contenido diferente → checksum diferente

    files_1 = {"file": ("doc1.pdf", pdf_1, "application/pdf")}
    files_2 = {"file": ("doc2.pdf", pdf_2, "application/pdf")}

    resp_1 = await async_client.post("/api/v1/documents/", files=files_1)
    resp_2 = await async_client.post("/api/v1/documents/", files=files_2)

    assert resp_1.status_code == 201
    assert resp_2.status_code == 201

    id_to_delete = resp_1.json()["id"]
    id_to_keep = resp_2.json()["id"]

    # Act — eliminar el primero
    delete_response = await async_client.delete(f"/api/v1/documents/{id_to_delete}")
    assert delete_response.status_code == 200

    # Assert — GET all solo trae el segundo
    get_all_response = await async_client.get("/api/v1/documents/")
    assert get_all_response.status_code == 200

    all_docs = get_all_response.json()
    all_ids = [doc["id"] for doc in all_docs]

    assert len(all_ids) == 1
    assert id_to_keep in all_ids
    assert id_to_delete not in all_ids


@pytest.mark.asyncio
async def test_delete_document_get_by_id_returns_404_after_deletion(async_client: AsyncClient, fake_pdf_bytes: bytes):
    """
    Dado: un documento existente que luego se elimina
    Cuando: se intenta obtener con GET /api/v1/documents/{id}
    Entonces: debe retornar 404 Not Found
    """
    # Arrange — subir y eliminar
    files = {"file": ("temporal.pdf", fake_pdf_bytes, "application/pdf")}
    upload_response = await async_client.post("/api/v1/documents/", files=files)
    assert upload_response.status_code == 201
    doc_id = upload_response.json()["id"]

    delete_response = await async_client.delete(f"/api/v1/documents/{doc_id}")
    assert delete_response.status_code == 200

    # Act — intentar obtener por ID
    get_response = await async_client.get(f"/api/v1/documents/{doc_id}")

    # Assert
    assert get_response.status_code == 404


@pytest.mark.asyncio
async def test_delete_allows_reupload_of_same_pdf(async_client: AsyncClient, fake_pdf_bytes: bytes):
    """
    Dado: un PDF subido y luego eliminado
    Cuando: se intenta subir el mismo PDF de nuevo (mismo checksum)
    Entonces: debe retornar 201 Created (el checksum ya no bloquea el duplicado)
    """
    # Arrange — subir y eliminar
    files = {"file": ("reciclable.pdf", fake_pdf_bytes, "application/pdf")}
    upload_1 = await async_client.post("/api/v1/documents/", files=files)
    assert upload_1.status_code == 201
    doc_id = upload_1.json()["id"]

    delete_response = await async_client.delete(f"/api/v1/documents/{doc_id}")
    assert delete_response.status_code == 200

    # Act — re-subir el mismo PDF
    files_again = {"file": ("reciclable_v2.pdf", fake_pdf_bytes, "application/pdf")}
    upload_2 = await async_client.post("/api/v1/documents/", files=files_again)

    # Assert — debe funcionar porque el documento fue eliminado
    assert upload_2.status_code == 201
    new_id = upload_2.json()["id"]
    assert new_id != doc_id  # Nuevo ID asignado por MongoDB