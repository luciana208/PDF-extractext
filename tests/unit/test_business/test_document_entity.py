"""
Tests unitarios para la entidad Document.

Valida que la entidad se construya correctamente, que sus campos tengan
los valores esperados y que los métodos de conveniencia funcionen bien.
"""

from datetime import datetime, timezone

import pytest

from app.business.entities.document import Document


class TestDocumentEntity:
    def test_creates_with_required_fields(self):
        """Debe crear una entidad válida con los campos mínimos."""
        doc = Document(
            filename="report.pdf",
            checksum="abc123",
            extracted_text="Sample text",
        )

        assert doc.filename == "report.pdf"
        assert doc.checksum == "abc123"
        assert doc.extracted_text == "Sample text"

    def test_id_is_none_before_persisting(self):
        """Antes de guardarse en la DB, el ID debe ser None."""
        doc = Document(filename="f.pdf", checksum="c", extracted_text="t")

        assert doc.id is None

    def test_is_persisted_returns_false_without_id(self):
        """is_persisted() debe retornar False si el ID es None."""
        doc = Document(filename="f.pdf", checksum="c", extracted_text="t")

        assert doc.is_persisted() is False

    def test_is_persisted_returns_true_with_id(self):
        """is_persisted() debe retornar True si el ID está asignado."""
        doc = Document(filename="f.pdf", checksum="c", extracted_text="t", id="some-id")

        assert doc.is_persisted() is True

    def test_created_at_is_set_automatically(self):
        """created_at debe ser asignado automáticamente al crear la entidad."""
        doc = Document(filename="f.pdf", checksum="c", extracted_text="t")

        assert isinstance(doc.created_at, datetime)

    def test_created_at_is_utc(self):
        """El timestamp de creación debe estar en UTC."""
        doc = Document(filename="f.pdf", checksum="c", extracted_text="t")

        assert doc.created_at.tzinfo == timezone.utc

    def test_accepts_empty_extracted_text(self):
        """Texto vacío es válido (PDF escaneado)."""
        doc = Document(filename="scanned.pdf", checksum="abc", extracted_text="")

        assert doc.extracted_text == ""