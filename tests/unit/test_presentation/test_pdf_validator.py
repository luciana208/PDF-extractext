"""
test_pdf_validator.py — Tests unitarios para pdf_validator.py
=============================================================
Estos tests verifican que el validador:
  1. Acepte archivos PDF válidos.
  2. Rechace archivos que no son PDF (magic bytes incorrectos).
  3. Rechace archivos que superan el tamaño máximo.

Se usan mocks de UploadFile para no depender de archivos reales en disco. Cada test es independiente: no comparte estado con otros tests.

Guía de testing (del profesor):
  - Un test por comportamiento esperado.
  - Nombre del test describe QUÉ se está probando y QUÉ se espera.
  - Sin lógica de negocio en los tests.
"""

import io
import pytest
from unittest.mock import AsyncMock, MagicMock
from fastapi import HTTPException

from app.presentation.validators.pdf_validator import (
    PDF_MAGIC_BYTES,
    validate_pdf,
)
from app.config.settings import settings


# ------------------------------------------------------------------ #
# Helpers: construcción de mocks de UploadFile                        #
# ------------------------------------------------------------------ #

def make_upload_file_mock(content: bytes) -> MagicMock:
    """
    Crea un mock de UploadFile que simula tener `content` como contenido.

    UploadFile tiene métodos async (read, seek), por eso usamos AsyncMock.
    La lógica de read() simula un cursor real: primer read devuelve los primeros 4 bytes, segundo read devuelve el resto.
    """
    mock = MagicMock()

    # Simulamos el cursor del archivo con un buffer de bytes.
    buffer = io.BytesIO(content)

    async def fake_read(n: int = -1) -> bytes:
        return buffer.read(n)

    async def fake_seek(pos: int) -> None:
        buffer.seek(pos)

    mock.read = fake_read
    mock.seek = fake_seek
    mock.size = len(content)  # ← NUEVO: FastAPI UploadFile tiene size
    return mock


# ------------------------------------------------------------------ #
# Tests                                                               #
# ------------------------------------------------------------------ #

class TestPdfValidator:
    """Agrupa todos los tests del pdf_validator."""

    @pytest.mark.asyncio
    async def test_valid_pdf_passes_validation(self):
        """
        Un archivo que empieza con %PDF y pesa menos del límite debe pasar la validación sin lanzar ninguna excepción.
        """
        # Construimos un PDF mínimo: magic bytes + contenido de relleno.
        valid_content = PDF_MAGIC_BYTES + b" fake pdf content"
        file_mock = make_upload_file_mock(valid_content)

        # No debe lanzar excepción.
        await validate_pdf(file_mock)

    @pytest.mark.asyncio
    async def test_non_pdf_file_raises_400(self):
        """
        Un archivo que NO empieza con %PDF debe lanzar HTTPException 400.
        Simula un usuario que sube un .docx renombrado como .pdf.
        """
        fake_docx_content = b"PK\x03\x04 not a pdf"
        file_mock = make_upload_file_mock(fake_docx_content)

        with pytest.raises(HTTPException) as exc_info:
            await validate_pdf(file_mock)

        assert exc_info.value.status_code == 400
        assert "no es un PDF válido" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_file_exceeding_max_size_raises_413(self):
        """
        Un archivo PDF real pero demasiado grande debe lanzar HTTPException 413 (Request Entity Too Large).
        """
        # Creamos contenido que supera el límite por 1 byte.
        oversized_content = PDF_MAGIC_BYTES + b"x" * (settings.MAX_PDF_SIZE_BYTES + 1)
        file_mock = make_upload_file_mock(oversized_content)

        with pytest.raises(HTTPException) as exc_info:
            await validate_pdf(file_mock)

        assert exc_info.value.status_code == 413

    @pytest.mark.asyncio
    async def test_file_at_exact_max_size_passes(self):
        """
        Un archivo PDF de exactamente el tamaño máximo debe pasar.
        Verifica que el límite es inclusivo (<=, no <).
        """
        # Tamaño exacto = MAX - 4 bytes de magic bytes.
        content_size = settings.MAX_PDF_SIZE_BYTES - len(PDF_MAGIC_BYTES)
        exact_size_content = PDF_MAGIC_BYTES + b"x" * content_size
        file_mock = make_upload_file_mock(exact_size_content)

        # No debe lanzar excepción.
        await validate_pdf(file_mock)

    @pytest.mark.asyncio
    async def test_seek_is_called_after_validation(self):
        """
        Después de validar, el cursor del archivo debe quedar en posición 0 para que el Service pueda leer el archivo completo.
        Verificamos que se llama seek(0).
        """
        valid_content = PDF_MAGIC_BYTES + b" content"
        mock = MagicMock()

        # Usamos buffer real para read pero AsyncMock para seek.
        buffer = io.BytesIO(valid_content)
        mock.read = AsyncMock(side_effect=lambda n=-1: buffer.read(n))
        mock.seek = AsyncMock()
        mock.size = len(valid_content)  # ← NUEVO

        await validate_pdf(mock)

        # Verificamos que seek fue llamado con 0.
        mock.seek.assert_any_call(0)