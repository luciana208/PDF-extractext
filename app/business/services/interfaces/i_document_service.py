from abc import ABC, abstractmethod
from app.business.entities.document import Document

class IDocumentService(ABC):
    """Interfaz del servicio principal de documentos.

    El Controller inyecta esta abstracción. La implementación real
    es DocumentService; en tests se puede inyectar un mock.
    """

    @abstractmethod
    async def process_pdf(self, file_bytes: bytes, filename: str) -> Document:
        """Procesa un PDF: extrae texto, calcula checksum y persiste.

        Es la operación más compleja del sistema. Orquesta la extracción,
        el cálculo de checksum, la detección de duplicados y el guardado.

        Args:
            file_bytes: Contenido binario del archivo PDF.
            filename: Nombre original del archivo subido por el usuario.

        Returns:
            La entidad Document con todos sus campos poblados.

        Raises:
            DuplicateDocumentError: Si ya existe un documento con el mismo checksum.
        """
        ...

    @abstractmethod
    async def get_all(self) -> list[Document]:
        """Retorna todos los documentos del sistema.

        Returns:
            Lista de entidades Document (puede estar vacía).
        """
        ...

    @abstractmethod
    async def get_by_id(self, document_id: str) -> Document:
        """Obtiene un documento por su ID.

        Args:
            document_id: Identificador único del documento.

        Returns:
            La entidad Document correspondiente.

        Raises:
            DocumentNotFoundError: Si no existe un documento con ese ID.
        """
        ...

    @abstractmethod
    async def update(self, document_id: str, fields: dict) -> Document:
        """Actualiza metadatos de un documento existente.

        Args:
            document_id: ID del documento a actualizar.
            fields: Campos a modificar (solo metadatos permitidos).

        Returns:
            La entidad Document con los datos actualizados.

        Raises:
            DocumentNotFoundError: Si no existe un documento con ese ID.
        """
        ...

    @abstractmethod
    async def delete(self, document_id: str) -> None:
        """Elimina un documento del sistema.

        Args:
            document_id: ID del documento a eliminar.

        Raises:
            DocumentNotFoundError: Si no existe un documento con ese ID.
        """
        ...