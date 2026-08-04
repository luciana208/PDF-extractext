"""
document_response.py — DTO de salida para respuestas al cliente
================================================================
Define exactamente qué información se le devuelve al cliente en cada respuesta. Actúa como "contrato de salida": el cliente puede depender
de esta estructura sin importar cómo esté guardado internamente.

Por qué es importante:
  - Desacopla la representación pública del modelo interno de la BD.
  - Si mañana cambia el modelo de MongoDB, la respuesta al cliente no cambia (mientras el Service construya bien este DTO).
  - LSP / DIP (SOLID): el cliente depende de esta abstracción, no del modelo concreto de persistencia.
"""

from datetime import datetime
from typing import TYPE_CHECKING

from pydantic import BaseModel, Field, computed_field

if TYPE_CHECKING:
    from app.business.entities.document import Document


class DocumentResponseDTO(BaseModel):
    id: str = Field(description="Identificador único del documento.")
    name: str = Field(description="Nombre del documento.")
    checksum: str = Field(description="Hash SHA-256 del archivo PDF.")
    extracted_text: str = Field(description="Texto extraído del PDF. Vacío si el PDF es escaneado.")
    created_at: datetime = Field(description="Fecha y hora de creación.")
    updated_at: datetime = Field(description="Fecha y hora de última modificación.")

    model_config = {
        "frozen": True,
        "json_encoders": {datetime: lambda v: v.isoformat()},
    }

    @computed_field(return_type=str)
    @property
    def text_preview(self) -> str:
        return self.extracted_text[:500]

    @classmethod
    def from_entity(cls, document: "Document") -> "DocumentResponseDTO":
        return cls(
            id=document.id,
            name=document.filename,   # ← entidad usa filename, DTO usa name
            checksum=document.checksum,
            extracted_text=document.extracted_text,
            created_at=document.created_at,
            updated_at=document.updated_at,
        )