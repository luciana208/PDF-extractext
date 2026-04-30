"""
upload_request.py — DTO de entrada para subir un PDF
=====================================================
Un DTO (Data Transfer Object) es un objeto cuyo único propósito es transportar datos desde el cliente hasta el sistema. No tiene lógica
de negocio: solo define la "forma" de los datos que se esperan recibir.

Principios aplicados:
  - SRP (SOLID): esta clase solo define el contrato de entrada.
  - KISS: mínima complejidad, solo lo necesario.
  - YAGNI: no se agregan campos que no se usan ahora.
"""

from pydantic import BaseModel, Field


class UploadRequestDTO(BaseModel):
    """
    Contrato de entrada cuando el cliente sube un PDF.

    En FastAPI, los archivos binarios (PDF) llegan como UploadFile directamente en el parámetro del endpoint, NO dentro de este DTO.
    Este DTO captura únicamente los metadatos opcionales que acompañan al archivo (por ejemplo, el nombre personalizado que le quiere dar
    el usuario).

    Campos:
        custom_name: nombre opcional que el usuario asigna al documento. Si no se envía, el sistema usará el nombre original del archivo.
    """

    custom_name: str | None = Field(
        default=None,
        description="Nombre personalizado para el documento (opcional).",
        max_length=255,
    )

    model_config = {"frozen": True}  # DTOs inmutables — acuerdo del equipo