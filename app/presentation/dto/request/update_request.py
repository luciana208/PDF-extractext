"""
update_request.py — DTO de entrada para actualizar metadatos de un documento
=============================================================================
Solo los campos de metadatos son actualizables. El contenido binario del PDF y el checksum calculado no se pueden modificar desde afuera: eso sería
lógica de negocio, no presentación.

Principios aplicados:
  - SRP: solo define qué campos acepta una actualización.
  - OCP (SOLID): si mañana se agrega un campo actualizable, se extiende esta clase sin romper nada existente.
  - YAGNI: no se exponen campos internos (checksum, extracted_text) que el cliente nunca debería modificar directamente.
"""

from pydantic import BaseModel, Field


class UpdateRequestDTO(BaseModel):
    """
    Contrato de entrada para actualizar metadatos de un documento existente.

    Todos los campos son opcionales (None por defecto): el cliente puede enviar solo los que quiere modificar (PATCH semántico).

    Campos:
        custom_name: nuevo nombre personalizado para el documento.
    """

    custom_name: str | None = Field(
        default=None,
        description="Nuevo nombre personalizado para el documento.",
        max_length=255,
    )

    model_config = {"frozen": True}  # DTOs inmutables — acuerdo del equipo