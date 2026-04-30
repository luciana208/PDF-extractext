"""
document_model.py
-----------------
Responsabilidad ÚNICA (SOLID - S): definir cómo se PERSISTE un documento
en MongoDB. Este modelo vive en la capa de Datos y NUNCA sale de ella;
las capas superiores trabajan con la entidad Document (capa de Negocio).
 
¿Qué hace este archivo?
  - Define el schema Pydantic que mapea la colección 'documents' de MongoDB.
  - Usa Beanie (ODM async sobre Motor) para simplificar las operaciones CRUD.
  - Convierte entre DocumentModel (persistencia) y Document (dominio) mediante
    métodos to_entity() y from_entity().
 
¿Por qué separar Model de Entity?
  - La entidad pertenece al negocio y no debe conocer MongoDB.
  - El modelo puede tener campos internos de BD (ej: _id, created_at)
    que no son relevantes para las reglas de negocio.
  - SOLID-D: si mañana cambiamos de MongoDB a PostgreSQL, solo
    modificamos esta capa.
"""
 
from datetime import datetime, timezone
 
from beanie import Document as BeanieDocument  # BeanieDocument maneja _id y la colección
from pydantic import Field
 
# Importamos la entidad de dominio para la conversión. Usamos TYPE_CHECKING
# para evitar importación circular en tiempo de ejecución.
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from app.business.entities.document import Document
 
 
class DocumentModel(BeanieDocument):
    """
    Representa un documento PDF guardado en MongoDB.
 
    Atributos:
        name        : Nombre original del archivo PDF subido.
        checksum    : SHA-256 del binario del PDF. Usado para detectar duplicados.
        extracted_text: Texto extraído del PDF. Puede ser vacío si el PDF es escaneado.
        created_at  : Timestamp UTC de creación. Lo asigna automáticamente la capa de Datos.
        updated_at  : Timestamp UTC de última modificación.
 
    Nota sobre `id`:
        Beanie hereda de BeanieDocument y expone `id` como alias de `_id` de Mongo.
        Al crear un documento nuevo sin id, Mongo genera un ObjectId automáticamente.
    """
 
    name: str
    checksum: str
    extracted_text: str = Field(default="")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
 
    class Settings:
        # Nombre de la colección en MongoDB
        name = "documents"
 
    # ------------------------------------------------------------------
    # Conversión Model ↔ Entity  (DRY: un único punto de transformación)
    # ------------------------------------------------------------------
 
    def to_entity(self) -> "Document":
        """
        Convierte este modelo de persistencia en la entidad de dominio.
        La capa de Negocio solo trabaja con entidades, nunca con modelos Mongo.
        """
        from app.business.entities.document import Document
 
        return Document(
            id=str(self.id),
            name=self.name,
            checksum=self.checksum,
            extracted_text=self.extracted_text,
            created_at=self.created_at,
            updated_at=self.updated_at,
        )
 
    @classmethod
    def from_entity(cls, entity: "Document") -> "DocumentModel":
        """
        Convierte una entidad de dominio en un modelo listo para persistir.
        Se usa en save() y update() del repositorio.
        """
        return cls(
            name=entity.name,
            checksum=entity.checksum,
            extracted_text=entity.extracted_text,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )
