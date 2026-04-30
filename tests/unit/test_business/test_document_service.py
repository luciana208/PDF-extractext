"""
Tests unitarios para DocumentService.

El Service se testea con un repositorio mockeado (pytest-mock / AsyncMock)
para que los tests sean rápidos y no dependan de MongoDB.

Patrón: Arrange → Act → Assert.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.business.domain.exceptions import DocumentNotFoundError, DuplicateDocumentError
from app.business.entities.document import Document
from app.business.services.document_service import DocumentService


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _make_document(**kwargs) -> Document:
    """Crea una entidad Document con valores por defecto sobreescribibles."""
    defaults = {
        "id": "doc-id-1",
        "filename": "test.pdf",
        "checksum": "a" * 64,
        "extracted_text": "Extracted content",
    }
    return Document(**{**defaults, **kwargs})


@pytest.fixture
def mock_repository() -> AsyncMock:
    """Mock del repositorio con todos los métodos como AsyncMock."""
    repo = AsyncMock()
    return repo


@pytest.fixture
def service(mock_repository: AsyncMock) -> DocumentService:
    """Instancia del service con repositorio mockeado inyectado."""
    return DocumentService(repository=mock_repository)


PDF_BYTES = b"%PDF-1.4 fake content for testing"


# ---------------------------------------------------------------------------
# process_pdf
# ---------------------------------------------------------------------------

class TestProcessPdf:
    async def test_saves_and_returns_document_when_new(
        self, service: DocumentService, mock_repository: AsyncMock
    ):
        """Si el PDF es nuevo (no duplicado), debe guardarlo y retornarlo."""
        mock_repository.get_by_checksum.return_value = None  # no existe aún
        expected_doc = _make_document()
        mock_repository.save.return_value = expected_doc

        with patch("app.business.services.document_service.extract_text", return_value="text"):
            result = await service.process_pdf(PDF_BYTES, "test.pdf")

        assert result == expected_doc
        mock_repository.save.assert_called_once()

    async def test_raises_duplicate_error_when_checksum_exists(
        self, service: DocumentService, mock_repository: AsyncMock
    ):
        """Si ya existe un documento con ese checksum, debe lanzar DuplicateDocumentError."""
        mock_repository.get_by_checksum.return_value = _make_document()

        with pytest.raises(DuplicateDocumentError):
            await service.process_pdf(PDF_BYTES, "copy.pdf")

        mock_repository.save.assert_not_called()

    async def test_does_not_extract_text_for_duplicates(
        self, service: DocumentService, mock_repository: AsyncMock
    ):
        """La extracción de texto (costosa) no debe ejecutarse si el PDF es duplicado."""
        mock_repository.get_by_checksum.return_value = _make_document()

        with patch("app.business.services.document_service.extract_text") as mock_extract:
            with pytest.raises(DuplicateDocumentError):
                await service.process_pdf(PDF_BYTES, "copy.pdf")

        mock_extract.assert_not_called()

    async def test_saves_with_empty_text_for_scanned_pdf(
        self, service: DocumentService, mock_repository: AsyncMock
    ):
        """Un PDF escaneado (sin texto) debe guardarse con extracted_text vacío."""
        mock_repository.get_by_checksum.return_value = None
        mock_repository.save.return_value = _make_document(extracted_text="")

        with patch("app.business.services.document_service.extract_text", return_value=""):
            result = await service.process_pdf(PDF_BYTES, "scanned.pdf")

        saved_doc = mock_repository.save.call_args[0][0]
        assert saved_doc.extracted_text == ""


# ---------------------------------------------------------------------------
# get_all
# ---------------------------------------------------------------------------

class TestGetAll:
    async def test_returns_list_of_documents(
        self, service: DocumentService, mock_repository: AsyncMock
    ):
        """Debe retornar la lista completa del repositorio."""
        docs = [_make_document(id="1"), _make_document(id="2")]
        mock_repository.get_all.return_value = docs

        result = await service.get_all()

        assert result == docs

    async def test_returns_empty_list_when_no_documents(
        self, service: DocumentService, mock_repository: AsyncMock
    ):
        """Debe retornar lista vacía si no hay documentos."""
        mock_repository.get_all.return_value = []

        result = await service.get_all()

        assert result == []


# ---------------------------------------------------------------------------
# get_by_id
# ---------------------------------------------------------------------------

class TestGetById:
    async def test_returns_document_when_found(
        self, service: DocumentService, mock_repository: AsyncMock
    ):
        """Debe retornar el documento cuando existe."""
        doc = _make_document()
        mock_repository.get_by_id.return_value = doc

        result = await service.get_by_id("doc-id-1")

        assert result == doc

    async def test_raises_not_found_when_missing(
        self, service: DocumentService, mock_repository: AsyncMock
    ):
        """Debe lanzar DocumentNotFoundError si el repositorio retorna None."""
        mock_repository.get_by_id.return_value = None

        with pytest.raises(DocumentNotFoundError) as exc_info:
            await service.get_by_id("non-existent-id")

        assert exc_info.value.document_id == "non-existent-id"


# ---------------------------------------------------------------------------
# update
# ---------------------------------------------------------------------------

class TestUpdate:
    async def test_returns_updated_document(
        self, service: DocumentService, mock_repository: AsyncMock
    ):
        """Debe retornar el documento con los campos actualizados."""
        updated = _make_document(filename="new-name.pdf")
        mock_repository.update.return_value = updated

        result = await service.update("doc-id-1", {"filename": "new-name.pdf"})

        assert result.filename == "new-name.pdf"

    async def test_raises_not_found_when_document_missing(
        self, service: DocumentService, mock_repository: AsyncMock
    ):
        """Debe lanzar DocumentNotFoundError si el repositorio retorna None."""
        mock_repository.update.return_value = None

        with pytest.raises(DocumentNotFoundError):
            await service.update("non-existent-id", {"filename": "x.pdf"})


# ---------------------------------------------------------------------------
# delete
# ---------------------------------------------------------------------------

class TestDelete:
    async def test_deletes_successfully(
        self, service: DocumentService, mock_repository: AsyncMock
    ):
        """Debe completarse sin excepción si el repositorio confirma la eliminación."""
        mock_repository.delete.return_value = True

        await service.delete("doc-id-1")  # No debe lanzar

        mock_repository.delete.assert_called_once_with("doc-id-1")

    async def test_raises_not_found_when_document_missing(
        self, service: DocumentService, mock_repository: AsyncMock
    ):
        """Debe lanzar DocumentNotFoundError si el repositorio indica que no existía."""
        mock_repository.delete.return_value = False

        with pytest.raises(DocumentNotFoundError):
            await service.delete("non-existent-id")