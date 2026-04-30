"""
Tests unitarios para text_extractor.

Valida el comportamiento del extractor con distintos tipos de PDF:
con texto, sin texto (escaneado) y PDF malformado.

Se usa unittest.mock para simular pdfplumber y no depender de archivos
reales en los tests unitarios. Los tests de integración usan sample.pdf.
"""

from unittest.mock import MagicMock, patch

import pytest

from app.business.domain.text_extractor import extract_text


class TestExtractText:
    def test_extracts_text_from_pdf_with_content(self):
        """Debe concatenar el texto de todas las páginas."""
        mock_page_1 = MagicMock()
        mock_page_1.extract_text.return_value = "Página uno"

        mock_page_2 = MagicMock()
        mock_page_2.extract_text.return_value = "Página dos"

        mock_pdf = MagicMock()
        mock_pdf.__enter__ = MagicMock(return_value=mock_pdf)
        mock_pdf.__exit__ = MagicMock(return_value=False)
        mock_pdf.pages = [mock_page_1, mock_page_2]

        with patch("app.business.domain.text_extractor.pdfplumber.open", return_value=mock_pdf):
            result = extract_text(b"fake-pdf-bytes")

        assert "Página uno" in result
        assert "Página dos" in result

    def test_returns_empty_string_when_pdf_has_no_text(self):
        """PDF escaneado (sin texto seleccionable) debe retornar '' sin lanzar excepción."""
        mock_page = MagicMock()
        mock_page.extract_text.return_value = None  # pdfplumber retorna None en páginas sin texto

        mock_pdf = MagicMock()
        mock_pdf.__enter__ = MagicMock(return_value=mock_pdf)
        mock_pdf.__exit__ = MagicMock(return_value=False)
        mock_pdf.pages = [mock_page]

        with patch("app.business.domain.text_extractor.pdfplumber.open", return_value=mock_pdf):
            result = extract_text(b"scanned-pdf-bytes")

        assert result == ""

    def test_does_not_raise_on_empty_pdf(self):
        """Un PDF sin páginas no debe lanzar excepción."""
        mock_pdf = MagicMock()
        mock_pdf.__enter__ = MagicMock(return_value=mock_pdf)
        mock_pdf.__exit__ = MagicMock(return_value=False)
        mock_pdf.pages = []

        with patch("app.business.domain.text_extractor.pdfplumber.open", return_value=mock_pdf):
            result = extract_text(b"empty-pdf-bytes")

        assert result == ""

    def test_returns_empty_string_on_extraction_error(self):
        """Si pdfplumber falla internamente, debe retornar '' en lugar de propagar la excepción."""
        with patch(
            "app.business.domain.text_extractor.pdfplumber.open",
            side_effect=Exception("Corrupt PDF"),
        ):
            result = extract_text(b"corrupt-bytes")

        assert result == ""

    def test_returns_string_type(self):
        """El resultado siempre debe ser un string, nunca None."""
        mock_pdf = MagicMock()
        mock_pdf.__enter__ = MagicMock(return_value=mock_pdf)
        mock_pdf.__exit__ = MagicMock(return_value=False)
        mock_pdf.pages = []

        with patch("app.business.domain.text_extractor.pdfplumber.open", return_value=mock_pdf):
            result = extract_text(b"any-bytes")

        assert isinstance(result, str)