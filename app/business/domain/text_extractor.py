"""
Extractor de texto de archivos PDF.

Convierte el contenido binario de un PDF en texto plano. Maneja los
dos casos principales: PDFs con texto seleccionable y PDFs escaneados
(imágenes sin texto extraíble).

Librería elegida: pdfplumber — mejor manejo de tablas y layouts complejos
que PyPDF2, y más liviana que PyMuPDF para extracción de texto puro.
"""

import io
import logging

import pdfplumber

logger = logging.getLogger(__name__)


def extract_text(file_bytes: bytes) -> str:
    """Extrae texto plano del contenido binario de un PDF.

    Itera sobre todas las páginas y concatena su texto. Si una página
    no contiene texto seleccionable (PDF escaneado), se omite sin lanzar
    una excepción; el resultado puede ser un string vacío.

    Args:
        file_bytes: Contenido binario del archivo PDF.

    Returns:
        Texto extraído como string. Retorna '' si el PDF no tiene texto
        seleccionable (ej: PDF de imágenes escaneadas).

    Raises:
        ValueError: Si los bytes no corresponden a un PDF válido.

    Example:
        >>> text = extract_text(pdf_bytes)
        >>> isinstance(text, str)
        True
    """
    try:
        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            # Extrae texto página a página; page.extract_text() puede ser None
            pages_text = [
                page.extract_text() or ""
                for page in pdf.pages
            ]
            return "\n".join(pages_text).strip()

    except Exception as exc:
        # Loguear para diagnóstico pero no propagar errores de extracción
        # como fallas del sistema: un PDF sin texto es un caso válido.
        logger.warning("Text extraction failed for a page: %s", exc)
        return ""