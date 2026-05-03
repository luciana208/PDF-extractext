"""
mongo_document_repository.py
-----------------------------
Responsabilidad ÚNICA (SOLID - S): implementar la interfaz de repositorio
usando MongoDB como motor de persistencia.

¿Qué hace este archivo?
  - Implementa i_document_repository.py (contrato definido por Dev 2).
  - Traduce operaciones de dominio (save, get_all, get_by_id, update, delete)
    a operaciones de MongoDB usando Beanie (ODM async).
  - Maneja los errores propios de la base de datos y los convierte en
    excepciones claras para la capa de Negocio.

Principio SOLID - O (Open/Closed):
  Si mañana cambiamos a PostgreSQL, creamos postgres_document_repository.py
  que también implemente i_document_repository.py. Este archivo no se toca.

Principio SOLID - L (Liskov Substitution):
  Esta clase puede reemplazar cualquier otro repositorio que implemente
  la misma interfaz sin que la capa de Negocio lo note.

Principio SOLID - D (Dependency Inversion):
  La capa de Negocio depende de la INTERFAZ, no de esta clase concreta.
  Esta clase es inyectada desde dependencies.py.
"""

import logging
from datetime import datetime, timezone

from beanie import PydanticObjectId
from pymongo.errors import DuplicateKeyError

from app.business.entities.document import Document
from app.business.repositories.interfaces.i_document_repository import IDocumentRepository
from app.data.dto.document_dto import DocumentDTO
from app.data.models.document_model import DocumentModel

logger = logging.getLogger(__name__)


class MongoDocumentRepository(IDocumentRepository):
    """
    Implementación concreta del repositorio usando MongoDB + Beanie.

    Beanie permite usar DocumentModel como si fuera un objeto Python normal:
      - await DocumentModel.insert()          → INSERT en Mongo
      - await DocumentModel.find_all().to_list() → SELECT * en Mongo
      - await DocumentModel.get(id)           → SELECT by _id en Mongo
      - await doc.set({...})                  → UPDATE en Mongo
      - await doc.delete()                    → DELETE en Mongo
    """

    async def save(self, document: Document) -> Document:
        """
        Persiste un nuevo documento en MongoDB.

        Flujo:
          1. Convierte la entidad a modelo Mongo (from_entity).
          2. Inserta el modelo (Beanie asigna el _id automáticamente).
          3. Convierte el modelo guardado de vuelta a entidad (to_entity)
             para que el servicio reciba el id generado.

        Raises:
            ValueError: si ya existe un documento con el mismo checksum (duplicado).
        """
        model = DocumentModel.from_entity(document)

        try:
            await model.insert()
        except DuplicateKeyError:
            # El índice único de 'checksum' rechaza duplicados
            logger.warning("Intento de guardar documento duplicado: checksum=%s", document.checksum)
            raise ValueError(f"Ya existe un documento con checksum {document.checksum}")

        logger.info("Documento guardado con id=%s", model.id)
        return model.to_entity()

    async def get_all(self) -> list[Document]:
        """
        Recupera todos los documentos de la colección.

        Retorna lista vacía si no hay documentos (nunca retorna None → KISS).
        """
        models = await DocumentModel.find_all().to_list()
        return [m.to_entity() for m in models]

    async def get_by_id(self, document_id: str) -> Document | None:
        """
        Busca un documento por su id de MongoDB.

        Args:
            document_id: string del ObjectId de Mongo (ej: "64a1b2c3d4e5f6a7b8c9d0e1").

        Returns:
            La entidad Document si existe, None si no existe.
            Retornar None en lugar de lanzar excepción es una decisión explícita:
            la capa de Negocio decide qué hacer cuando no encuentra el documento.
        """
        try:
            object_id = PydanticObjectId(document_id)
        except Exception:
            # Si el id no tiene formato válido de ObjectId, no puede existir
            logger.debug("document_id con formato inválido: %s", document_id)
            return None

        model = await DocumentModel.get(object_id)
        return model.to_entity() if model else None

    async def get_by_checksum(self, checksum: str) -> Document | None:
        """
        Busca un documento por su SHA-256.
        Usado por la capa de Negocio para detectar duplicados antes de guardar.

        Returns:
            La entidad Document si existe, None si no existe.
        """
        model = await DocumentModel.find_one(DocumentModel.checksum == checksum)
        return model.to_entity() if model else None

    async def update(self, document_id: str, fields: dict) -> Document | None:
        """
        Actualiza los metadatos de un documento existente.

        Solo permite actualizar campos de metadatos (ej: filename).
        El checksum y el texto extraído son inmutables por diseño del dominio.
        """
        try:
            object_id = PydanticObjectId(document_id)
        except Exception:
            logger.debug("document_id con formato inválido: %s", document_id)
            return None

        model = await DocumentModel.get(object_id)
        if not model:
            logger.warning("Update fallido: documento no encontrado id=%s", document_id)
            return None

        # Solo campos permitidos (metadatos) - KISS: no exponer campos internos
        update_data = {}
        if "filename" in fields:
            update_data[DocumentModel.name] = fields["filename"]
        
        update_data[DocumentModel.updated_at] = datetime.now(timezone.utc)

        await model.set(update_data)
        logger.info("Documento actualizado id=%s", document_id)
        return model.to_entity()

    async def delete(self, document_id: str) -> bool:
        """
        Elimina un documento por su id.

        Returns:
            True si el documento existía y fue eliminado.
            False si no existía (la capa de Negocio decide si es error o no).
        """
        try:
            object_id = PydanticObjectId(document_id)
        except Exception:
            return False

        model = await DocumentModel.get(object_id)
        if not model:
            logger.warning("Delete fallido: documento no encontrado id=%s", document_id)
            return False

        await model.delete()
        logger.info("Documento eliminado id=%s", document_id)
        return True