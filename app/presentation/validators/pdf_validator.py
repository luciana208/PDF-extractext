"""
pdf_validator.py — Validador de archivos PDF
============================================
Responsabilidad única: determinar si un archivo es un PDF real y si cumple con el tamaño máximo permitido.

¿Por qué validar con "magic bytes" y no solo con la extensión?
  Un usuario podría renombrar cualquier archivo como "documento.pdf".
  Los magic bytes son los primeros bytes del archivo y no mienten: todo PDF válido empieza con la secuencia b'%PDF'.

¿Por qué está en la capa de Presentación?
  Esta es una validación de FORMATO/SUPERFICIE, no de negocio.
  La capa de Presentación descarta basura antes de molestar al Service.

Principios aplicados:
  - SRP: solo valida, no procesa ni guarda.
  - KISS: dos funciones simples, sin abstracciones innecesarias.
  - DRY: la lógica de magic bytes está en un solo lugar.
"""

from fastapi import UploadFile

from app.business.domain.exceptions import InvalidFileError
from app.config.settings import settings

# Los primeros 4 bytes de todo archivo PDF válido (firma del formato).
PDF_MAGIC_BYTES: bytes = b"%PDF"


async def validate_pdf(file: UploadFile) -> None:
    """
    Valida que el archivo recibido sea un PDF real y no supere el tamaño
    máximo configurado.

    Lee solo los primeros 4 bytes para verificar la firma (magic bytes) y
    usa seek() para obtener el tamaño total sin cargar el archivo en memoria.
    Al terminar, rebobina el cursor para que el siguiente módulo pueda leerlo
    completo desde el principio.

    Args:
        file: El archivo subido por el cliente (FastAPI UploadFile).

    Raises:
        HTTPException 400: Si el archivo no es un PDF válido.
        HTTPException 413: Si el archivo supera el tamaño máximo.
    """
    # — Paso 1: verificar magic bytes —
    # Leemos solo 4 bytes; es suficiente para confirmar la firma PDF.
    header = await file.read(4)
    if header != PDF_MAGIC_BYTES:
        raise InvalidFileError("El archivo no es un PDF válido.", status_code=400)

    # — Paso 2: calcular tamaño total sin leer contenido —
    # FastAPI UploadFile.seek() solo acepta offset, no whence.
    # Usamos read() para consumir todo y medir, o confiamos en file.size si está disponible.
    # Optimización: si file.size existe (Starlette lo setea), lo usamos directamente.
    if hasattr(file, 'size') and file.size is not None:
        total_size = file.size
    else:
        # Fallback: leer todo el contenido para medir (menos eficiente pero funciona)
        current_pos = len(header)
        while True:
            chunk = await file.read(8192)
            if not chunk:
                break
            current_pos += len(chunk)
        total_size = current_pos

    # — Paso 3: rebobinar para el siguiente lector —
    await file.seek(0)

    if total_size > settings.MAX_PDF_SIZE_BYTES:
        raise InvalidFileError(
            f"El archivo supera el tamaño máximo de {settings.MAX_PDF_SIZE_MB} MB.",
            status_code=413,
        )