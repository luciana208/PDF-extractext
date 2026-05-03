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

from fastapi import HTTPException, UploadFile, status

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
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El archivo no es un PDF válido.",
        )

    # — Paso 2: calcular tamaño total sin leer contenido —
    # Usamos seek() para mover el cursor al final y obtener la posición.
    # Esto evita cargar todo el archivo en memoria (optimización de rendimiento).
    await file.seek(0, 2)  # 2 = SEEK_END (ir al final del archivo)
    total_size = await file.tell()
    await file.seek(0)     # Volver al inicio para el siguiente lector

    if total_size > settings.MAX_PDF_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"El archivo supera el tamaño máximo de "
                   f"{settings.MAX_PDF_SIZE_MB} MB.",
        )