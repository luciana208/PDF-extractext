"""
Validador de reglas de negocio para documentos.

Contiene las validaciones que van más allá del formato (eso lo hace
pdf_validator en Presentación). Aquí se validan reglas de dominio:
duplicados, integridad de datos, campos obligatorios.

Separado del Service para respetar SRP: el Service orquesta, el
Validator evalúa reglas.
"""

from app.business.domain.exceptions import DuplicateDocumentError
from app.business.entities.document import Document


def validate_no_duplicate(existing_document: Document | None, checksum: str) -> None:
    """Verifica que no exista ya un documento con el mismo checksum.

    Se llama antes de persistir un nuevo documento. Si ya hay uno con
    el mismo SHA-256, lanza la excepción que la Presentación traduce a 409.

    Args:
        existing_document: Resultado de buscar por checksum en el repositorio.
                           None significa que el documento es nuevo.
        checksum: Hash SHA-256 del archivo que se intenta guardar.

    Raises:
        DuplicateDocumentError: Si `existing_document` no es None.
    """
    if existing_document is not None:
        raise DuplicateDocumentError(checksum)