"""
Servicio principal de documentos.


"""

import logging

from app.business.domain.checksum_calculator import calculate_checksum
from app.business.domain.exceptions import DocumentNotFoundError
from app.business.domain.text_extractor import extract_text
from app.business.domain.validators.document_validator import validate_no_duplicate
from app.business.entities.document import Document
from app.business.repositories.interfaces.i_document_repository import IDocumentRepository
from app.business.services.interfaces.i_document_service import IDocumentService

logger = logging.getLogger(__name__)


class DocumentService(IDocumentService):
    """Implementación del servicio de documentos.

    Recibe el repositorio por inyección de dependencias (dependencies.py),
    lo que permite sustituirlo por un mock en tests sin modificar esta clase.
    """

    def __init__(self, repository: IDocumentRepository) -> None:
        """Inicializa el servicio con su repositorio.

        Args:
            repository: Implementación concreta del repositorio de documentos.
                        En producción: MongoDocumentRepository.
                        En tests: un MagicMock o implementación en memoria.
        """
        self._repository = repository

    async def process_pdf(self, file_bytes: bytes, filename: str) -> Document:
        """Procesa un PDF: calcula checksum, extrae texto, detecta duplicados y persiste.

        Flujo:
            1. Calcula SHA-256 del archivo (idempotente, sin I/O).
            2. Consulta al repositorio si ya existe ese checksum.
            3. Lanza DuplicateDocumentError si es duplicado.
            4. Extrae el texto del PDF.
            5. Construye la entidad Document.
            6. Persiste y retorna la entidad con ID.

        Args:
            file_bytes: Contenido binario del PDF.
            filename: Nombre original del archivo.

        Returns:
            Document persistido con todos sus campos poblados.

        Raises:
            DuplicateDocumentError: Si ya existe un PDF con el mismo contenido.
        """
        checksum = calculate_checksum(file_bytes)

        # Verificar duplicado antes de extraer texto (operación costosa)
        existing = await self._repository.get_by_checksum(checksum)
        validate_no_duplicate(existing, checksum)

        extracted_text = extract_text(file_bytes)
        logger.info("Processed '%s': %d chars extracted.", filename, len(extracted_text))

        document = Document(
            filename=filename,
            checksum=checksum,
            extracted_text=extracted_text,
        )

        return await self._repository.save(document)

    async def get_all(self, skip: int = 0, limit: int = 20) -> list[Document]:
        """Retorna documentos almacenados con paginación.

        Args:
            skip: Documentos a saltar (offset).
            limit: Máximo de documentos por página.

        Returns:
            Lista de entidades Document (puede estar vacía).
        """
        return await self._repository.get_all(skip=skip, limit=limit)

    async def get_by_id(self, document_id: str) -> Document:
        """Obtiene un documento por su ID.

        Args:
            document_id: Identificador único del documento.

        Returns:
            Entidad Document correspondiente al ID.

        Raises:
            DocumentNotFoundError: Si no existe ningún documento con ese ID.
        """
        document = await self._repository.get_by_id(document_id)
        if document is None:
            raise DocumentNotFoundError(document_id)
        return document

    async def get_text(self, document_id: str) -> Document:
        """Retorna la entidad Document necesaria para descargar el texto.

        Implementado como alias de `get_by_id` para dejar claro el propósito.
        """
        return await self.get_by_id(document_id)

    async def update(self, document_id: str, fields: dict) -> Document:
        """Actualiza metadatos de un documento.

        Solo permite actualizar campos de metadatos (ej: filename).
        El checksum y el texto extraído son inmutables.

        Args:
            document_id: ID del documento a actualizar.
            fields: Diccionario con los campos y valores a modificar.

        Returns:
            Entidad Document con los datos actualizados.

        Raises:
            DocumentNotFoundError: Si no existe ningún documento con ese ID.
        """
        updated = await self._repository.update(document_id, fields)
        if updated is None:
            raise DocumentNotFoundError(document_id)
        return updated

    async def delete(self, document_id: str) -> None:
        """Elimina un documento del sistema.

        Args:
            document_id: ID del documento a eliminar.

        Raises:
            DocumentNotFoundError: Si no existe ningún documento con ese ID.
        """
        deleted = await self._repository.delete(document_id)
        if not deleted:
            raise DocumentNotFoundError(document_id)

        logger.info("Document '%s' deleted.", document_id)