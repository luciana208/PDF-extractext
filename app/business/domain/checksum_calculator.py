import hashlib

def calculate_checksum(file_bytes: bytes) -> str:
    """Calcula el hash SHA-256 del contenido binario de un archivo.

    Es una función pura e idempotente: el mismo input siempre produce
    el mismo output, y no modifica ningún estado externo.

    Args:
        file_bytes: Contenido binario del archivo a procesar.

    Returns:
        Hash SHA-256 expresado como string hexadecimal de 64 caracteres.

    Example:
        >>> checksum = calculate_checksum(b"contenido del pdf")
        >>> len(checksum)
        64
    """
    return hashlib.sha256(file_bytes).hexdigest()