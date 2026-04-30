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

from pydantic import BaseModel, Field


class DocumentResponseDTO(BaseModel):
    """
    Estructura de la respuesta JSON que el cliente recibe para un documento.

    Campos:
        id:             Identificador único (string del ObjectId de MongoDB).
        name:           Nombre del documento (custom_name o nombre original).
        checksum:       Hash SHA-256 del archivo; permite detectar duplicados.
        extracted_text: Texto extraído del PDF (puede ser vacío si es escaneado).
        created_at:     Fecha/hora de creación en formato ISO 8601.
        updated_at:     Fecha/hora de la última modificación.
    """

    id: str = Field(description="Identificador único del documento.")
    name: str = Field(description="Nombre del documento.")
    checksum: str = Field(description="Hash SHA-256 del archivo PDF.")
    extracted_text: str = Field(
        description="Texto extraído del PDF. Vacío si el PDF es escaneado."
    )
    created_at: datetime = Field(description="Fecha y hora de creación.")
    updated_at: datetime = Field(description="Fecha y hora de última modificación.")

    model_config = {
        "frozen": True,          # DTOs inmutables — acuerdo del equipo
        "json_encoders": {datetime: lambda v: v.isoformat()},
    }