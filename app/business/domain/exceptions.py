"""
Excepciones de dominio de la capa de Negocio.

Centralizar las excepciones aquí evita duplicación (DRY) y permite
que la capa de Presentación las capture con precisión para devolver
el código HTTP correcto.

Regla: las excepciones de negocio NO importan nada de FastAPI ni de MongoDB.
Son excepciones Python puras, reutilizables en cualquier contexto.
"""


class DocumentNotFoundError(Exception):
    """Se lanza cuando se busca un documento que no existe en el sistema.

    La capa de Presentación debe traducir esta excepción a HTTP 404.
    """

    def __init__(self, document_id: str) -> None:
        super().__init__(f"Document '{document_id}' not found.")
        self.document_id = document_id


class DuplicateDocumentError(Exception):
    """Se lanza cuando se intenta guardar un PDF ya existente (mismo checksum).

    La capa de Presentación debe traducir esta excepción a HTTP 409 Conflict.
    """

    def __init__(self, checksum: str) -> None:
        super().__init__(f"A document with checksum '{checksum}' already exists.")
        self.checksum = checksum