"""
document_dto.py
---------------
Responsabilidad ÚNICA (SOLID - S): transportar datos entre la capa de Negocio
y la capa de Datos SIN acoplar ambas capas.

¿Qué es un DTO?
  DTO = Data Transfer Object. Es un objeto simple que solo tiene datos,
  sin lógica de negocio ni lógica de persistencia. Es como una "bolsa"
  que lleva información de un lado al otro.

¿Por qué existe si ya hay Model y Entity?
  - La entidad (business) puede evolucionar con lógica de dominio.
  - El modelo (data) puede tener campos internos de Mongo (_id, índices).
  - El DTO es un punto de estabilidad: si cambia la entidad o el modelo,
    solo se actualiza este archivo, no toda la cadena (DRY).

Principio YAGNI aplicado: el DTO solo tiene los campos que realmente
se intercambian entre capas. No agregamos campos "por si acaso".
"""

from dataclasses import dataclass
from datetime import datetime

# Importamos TYPE_CHECKING para evitar circular imports
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from app.business.entities.document import Document
    from app.data.models.document_model import DocumentModel


@dataclass(frozen=True)  # frozen=True: inmutable según acuerdos del equipo (workflow_equipo.docx §5.1)
class DocumentDTO:
    """
    Objeto de transferencia entre la capa de Negocio y la capa de Datos.

    Atributos:
        id            : Identificador único (str del ObjectId de Mongo). None si aún no fue guardado.
        name          : Nombre del archivo PDF.
        checksum      : SHA-256 del archivo.
        extracted_text: Texto extraído del PDF.
        created_at    : Fecha de creación.
        updated_at    : Fecha de última modificación.
    """

    id: str | None
    name: str
    checksum: str
    extracted_text: str
    created_at: datetime
    updated_at: datetime

    # ------------------------------------------------------------------
    # Conversión DTO ↔ Entity  (un único punto de transformación → DRY)
    # ------------------------------------------------------------------

    @classmethod
    def from_entity(cls, entity: "Document") -> "DocumentDTO":
        """
        Crea un DTO a partir de una entidad de dominio.
        Usado cuando el servicio le pasa datos al repositorio.
        """
        return cls(
            id=entity.id,
            name=entity.filename,
            checksum=entity.checksum,
            extracted_text=entity.extracted_text,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )

    def to_entity(self) -> "Document":
        """
        Reconstruye la entidad de dominio desde el DTO.
        Usado cuando el repositorio le devuelve datos al servicio.
        """
        from app.business.entities.document import Document

        return Document(
            id=self.id,
            filename =self.name,
            checksum=self.checksum,
            extracted_text=self.extracted_text,
            created_at=self.created_at,
            updated_at=self.updated_at,
        )

    @classmethod
    def from_model(cls, model: "DocumentModel") -> "DocumentDTO":
        """
        Crea un DTO a partir del modelo Mongo.
        Esto permite que el repositorio no devuelva modelos Mongo directamente.
        """
        return cls(
            id=str(model.id),
            name=model.name,
            checksum=model.checksum,
            extracted_text=model.extracted_text,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )