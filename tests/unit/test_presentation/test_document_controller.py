"""
test_document_controller.py — Tests unitarios para document_controller.py
=========================================================================
Estos tests verifican que el Controller:
  1. Llama al Service con los datos correctos.
  2. Devuelve la respuesta correcta cuando el Service tiene éxito.
  3. Lanza HTTPException apropiada cuando el Service no encuentra un recurso.

Se usa unittest.mock para reemplazar el Service con un mock, de modo que estos tests solo prueban la lógica del Controller, no del Service.
"""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException

from app.business.entities.document import Document
from app.business.domain.exceptions import DocumentNotFoundError
from app.presentation.controllers.document_controller import DocumentController
from app.presentation.dto.request.update_request import UpdateRequestDTO
from app.presentation.dto.request.upload_request import UploadRequestDTO
from app.presentation.dto.response.document_response import DocumentResponseDTO


# ------------------------------------------------------------------ #
# Fixtures
# ------------------------------------------------------------------ #

@pytest.fixture
def sample_entity() -> Document:
    """Entidad de dominio de ejemplo."""
    return Document(
        id="abc123",
        filename="Documento de prueba",
        checksum="sha256fakehash",
        extracted_text="Texto extraído del PDF de prueba.",
        created_at=datetime(2024, 1, 1, 12, 0, 0),
        updated_at=datetime(2024, 1, 1, 12, 0, 0),
    )


@pytest.fixture
def sample_response() -> DocumentResponseDTO:
    """DTO de respuesta de ejemplo."""
    return DocumentResponseDTO(
        id="abc123",
        name="Documento de prueba",
        checksum="sha256fakehash",
        extracted_text="Texto extraído del PDF de prueba.",
        created_at=datetime(2024, 1, 1, 12, 0, 0),
        updated_at=datetime(2024, 1, 1, 12, 0, 0),
    )


@pytest.fixture
def mock_service(sample_entity) -> MagicMock:
    """Mock del IDocumentService con todos los métodos configurados."""
    # Create individual use case mocks
    process = MagicMock()
    process.execute = AsyncMock(return_value=sample_entity)
    list_uc = MagicMock()
    list_uc.execute = AsyncMock(return_value=[sample_entity])
    get_uc = MagicMock()
    get_uc.execute = AsyncMock(return_value=sample_entity)
    update_uc = MagicMock()
    update_uc.execute = AsyncMock(return_value=sample_entity)
    delete_uc = MagicMock()
    delete_uc.execute = AsyncMock(return_value=True)
    download_uc = MagicMock()
    download_uc.execute = AsyncMock(return_value=sample_entity)

    return {
        "process": process,
        "list": list_uc,
        "get": get_uc,
        "update": update_uc,
        "delete": delete_uc,
        "download": download_uc,
    }


@pytest.fixture
def controller(mock_service) -> DocumentController:
    """Controller con el service mockeado inyectado."""
    return DocumentController(
        process_pdf=mock_service["process"],
        list_documents=mock_service["list"],
        get_document=mock_service["get"],
        update_document=mock_service["update"],
        delete_document=mock_service["delete"],
        download_text=mock_service["download"],
    )


# ------------------------------------------------------------------ #
# Tests — upload_document
# ------------------------------------------------------------------ #

class TestUploadDocument:

    @pytest.mark.asyncio
    async def test_upload_calls_validate_and_service(self, controller, mock_service, sample_response, sample_entity):
        """
        El controller debe validar el PDF y luego llamar al service.
        Como el archivo tiene magic bytes válidos, la validación debe pasar.
        """
        import io
        from fastapi import UploadFile

        valid_pdf = b"%PDF fake content"
        file_mock = MagicMock(spec=UploadFile)
        buffer = io.BytesIO(valid_pdf)
        file_mock.read = AsyncMock(side_effect=lambda n=-1: buffer.read(n))
        file_mock.seek = AsyncMock()
        file_mock.tell = AsyncMock(return_value=len(valid_pdf))

        dto = UploadRequestDTO(custom_name="Mi documento")

        result = await controller.upload_document(file_mock, dto)

        mock_service["process"].execute.assert_called_once()
        assert result == sample_response
        assert result.text_preview == sample_entity.extracted_text


# ------------------------------------------------------------------ #
# Tests — get_all_documents
# ------------------------------------------------------------------ #

class TestGetAllDocuments:

    @pytest.mark.asyncio
    async def test_returns_list_from_service(self, controller, mock_service, sample_response):
        """El controller debe devolver la lista que retorna el service."""
        result = await controller.get_all_documents()

        mock_service["list"].execute.assert_called_once()
        assert result == [sample_response]

    @pytest.mark.asyncio
    async def test_returns_empty_list_when_no_documents(self, controller, mock_service):
        """Si el service devuelve lista vacía, el controller también debe devolver lista vacía."""
        mock_service["list"].execute = AsyncMock(return_value=[])

        result = await controller.get_all_documents()

        assert result == []


# ------------------------------------------------------------------ #
# Tests — get_document_by_id
# ------------------------------------------------------------------ #

class TestGetDocumentById:

    @pytest.mark.asyncio
    async def test_returns_document_when_found(self, controller, mock_service, sample_response):
        """Si el service encuentra el documento, el controller lo devuelve."""
        result = await controller.get_document_by_id("abc123")

        mock_service["get"].execute.assert_called_once_with("abc123")
        assert result == sample_response

    @pytest.mark.asyncio
    async def test_raises_404_when_not_found(self, controller, mock_service):
        """Si el service lanza DocumentNotFoundError, el controller debe lanzar HTTPException 404."""
        mock_service["get"].execute = AsyncMock(side_effect=DocumentNotFoundError("id_inexistente"))

        with pytest.raises(HTTPException) as exc_info:
            await controller.get_document_by_id("id_inexistente")

        assert exc_info.value.status_code == 404
        assert "id_inexistente" in exc_info.value.detail


# ------------------------------------------------------------------ #
# Tests — update_document
# ------------------------------------------------------------------ #

class TestUpdateDocument:

    @pytest.mark.asyncio
    async def test_returns_updated_document(self, controller, mock_service, sample_response):
        """Si el service actualiza correctamente, el controller devuelve el documento actualizado."""
        dto = UpdateRequestDTO(custom_name="Nuevo nombre")

        result = await controller.update_document("abc123", dto)

        mock_service["update"].execute.assert_called_once_with("abc123", {"custom_name": "Nuevo nombre"})
        assert result == sample_response

    @pytest.mark.asyncio
    async def test_raises_404_when_document_not_found(self, controller, mock_service):
        """Si el service lanza DocumentNotFoundError en update, el controller lanza 404."""
        mock_service["update"].execute = AsyncMock(side_effect=DocumentNotFoundError("id_inexistente"))
        dto = UpdateRequestDTO(custom_name="Nuevo nombre")

        with pytest.raises(HTTPException) as exc_info:
            await controller.update_document("id_inexistente", dto)

        assert exc_info.value.status_code == 404


# ------------------------------------------------------------------ #
# Tests — delete_document
# ------------------------------------------------------------------ #

class TestDeleteDocument:

    @pytest.mark.asyncio
    async def test_returns_confirmation_message(self, controller, mock_service):
        """Si el service elimina correctamente, el controller devuelve mensaje de confirmación."""
        result = await controller.delete_document("abc123")

        mock_service["delete"].execute.assert_called_once_with("abc123")
        assert "abc123" in result["message"]

    @pytest.mark.asyncio
    async def test_raises_404_when_document_not_found(self, controller, mock_service):
        """Si el service lanza DocumentNotFoundError, el controller lanza 404."""
        mock_service["delete"].execute = AsyncMock(side_effect=DocumentNotFoundError("id_inexistente"))

        with pytest.raises(HTTPException) as exc_info:
            await controller.delete_document("id_inexistente")

        assert exc_info.value.status_code == 404