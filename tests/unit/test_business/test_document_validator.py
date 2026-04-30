"""
Tests unitarios para document_validator.

Valida la lógica de detección de duplicados: si el repositorio ya
tiene un documento con el mismo checksum, debe lanzar DuplicateDocumentError.
"""

import pytest

from app.business.domain.exceptions import DuplicateDocumentError
from app.business.domain.validators.document_validator import validate_no_duplicate
from app.business.entities.document import Document


def _make_document() -> Document:
    """Fixture helper: crea un Document con datos mínimos válidos."""
    return Document(
        id="existing-id",
        filename="existing.pdf",
        checksum="abc123",
        extracted_text="Some text",
    )


class TestValidateNoDuplicate:
    def test_passes_when_no_existing_document(self):
        """Si el repositorio no encontró nada (None), no debe lanzar excepción."""
        # No debe lanzar
        validate_no_duplicate(existing_document=None, checksum="any-checksum")

    def test_raises_when_document_already_exists(self):
        """Si ya existe un documento con ese checksum, debe lanzar DuplicateDocumentError."""
        existing = _make_document()

        with pytest.raises(DuplicateDocumentError):
            validate_no_duplicate(existing_document=existing, checksum="abc123")

    def test_error_contains_the_checksum(self):
        """El error debe incluir el checksum para facilitar el diagnóstico."""
        checksum = "deadbeef" * 8
        existing = _make_document()

        with pytest.raises(DuplicateDocumentError) as exc_info:
            validate_no_duplicate(existing_document=existing, checksum=checksum)

        assert checksum in str(exc_info.value)
        assert exc_info.value.checksum == checksum