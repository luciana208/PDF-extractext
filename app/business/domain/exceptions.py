"""Excepciones de negocio para los documentos."""

from fastapi import HTTPException


class ProblemDetailError(HTTPException):
    """Excepción HTTP compatible con Problem Details (RFC 9457)."""

    def __init__(self, status_code: int, title: str, detail: str, type_: str = "about:blank") -> None:
        super().__init__(status_code=status_code, detail=detail)
        self.title = title
        self.type = type_


class DocumentNotFoundError(ProblemDetailError):
    """Se lanza cuando se busca un documento que no existe en el sistema."""

    def __init__(self, document_id: str) -> None:
        super().__init__(status_code=404, title="Not Found", detail=f"Document '{document_id}' not found.")
        self.document_id = document_id


class DuplicatePDFError(ProblemDetailError):
    """Se lanza cuando se intenta guardar un PDF ya existente (mismo checksum)."""

    def __init__(self, checksum: str) -> None:
        super().__init__(status_code=409, title="Conflict", detail=f"A document with checksum '{checksum}' already exists.")
        self.checksum = checksum


class DuplicateDocumentError(DuplicatePDFError):
    """Alias de compatibilidad para el flujo actual del servicio."""

    pass


class InvalidFileError(ProblemDetailError):
    """Se lanza cuando el archivo enviado no es un PDF válido o supera el límite."""

    def __init__(self, detail: str, status_code: int = 400) -> None:
        title = "Bad Request" if status_code == 400 else "Payload Too Large"
        super().__init__(status_code=status_code, title=title, detail=detail)