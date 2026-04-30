from ABC import ABC, abstractmethod
from typing import Optional
from app.business.entities.document import Document 

class IDocumentRepository(ABC):

    """Interfaz del repositorio de documentos.

    Toda implementación concreta (Mongo, SQL, en memoria) debe heredar
    esta clase y proveer los cinco métodos CRUD.
    """
    @abstractmethod
    async def save(self, document: Document) -> Document:
        """Persiste un documento nuevo y retorna la entidad con el ID asignado.

        Args:
            document: Entidad de dominio lista para guardar.

        Returns:
            La misma entidad con el campo `id` poblado por la DB.
        """
        ...
    @abstractmethod
    async def get_all(self) -> list[Document]:
        """Retorna todos los documentos almacenados.

        Returns:
            Lista (puede estar vacía) de entidades Document.
        """
        ...

    @abstractmethod
    async def get_by_id(self, document_id: str) -> Optional[Document]:
        """Busca un documento por su ID único.

        Args:
            document_id: Identificador único del documento (string del ObjectId).

        Returns:
            La entidad si existe, None si no se encuentra.
        """
        ...

    @abstractmethod
    async def get_by_checksum(self, checksum: str) -> Optional[Document]:
        """Busca un documento por su checksum SHA-256.

        Necesario para detección de duplicados antes de persistir.

        Args:
            checksum: Hash SHA-256 del contenido del archivo.

        Returns:
            La entidad si existe un documento con ese checksum, None si es nuevo.
        """
        ...

    @abstractmethod
    async def update(self, document_id: str, fields: dict) -> Optional[Document]:
        """Actualiza campos específicos de un documento existente.

        Solo permite actualizar metadatos (ej: filename). El checksum
        y el texto extraído son inmutables una vez persistidos.

        Args:
            document_id: ID del documento a actualizar.
            fields: Diccionario con los campos a modificar y sus nuevos valores.

        Returns:
            La entidad actualizada, o None si no se encontró el documento.
        """
        ...

    @abstractmethod
    async def delete(self, document_id: str) -> bool:
        """Elimina un documento por su ID.

        Args:
            document_id: ID del documento a eliminar.

        Returns:
            True si el documento existía y fue eliminado, False si no existía.
        """
        ...