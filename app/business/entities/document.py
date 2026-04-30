"""
Entidad de dominio: Document.

Representa un documento PDF dentro del sistema. Es un objeto puro de Python,
sin dependencias de frameworks ni de bases de datos. Vive exclusivamente
en la capa de Negocio.

Esta entidad es el "lenguaje" que hablan las capas entre sí. Tanto el
Service como el Repository trabajan con objetos Document, nunca con
dicts crudos ni modelos de MongoDB.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class Document:
    """Objeto de dominio que representa un PDF procesado.

    Es inmutable por diseño: una vez creado, sus campos de contenido
    (checksum, extracted_text) no deberían cambiar. Solo los metadatos
    (filename) son actualizables.

    Attributes:
        filename: Nombre original del archivo subido.
        checksum: Hash SHA-256 del contenido binario del PDF.
        extracted_text: Texto puro extraído del PDF (vacío si es escaneado).
        id: Identificador único asignado por la base de datos (None antes de persistir).
        created_at: Timestamp de creación (UTC).
        updated_at: Timestamp de última actualización (UTC).
    """

    filename: str
    checksum: str
    extracted_text: str

    # Campos opcionales: None antes de persistir, poblados por el repositorio
    id: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def is_persisted(self) -> bool:
        """Indica si el documento ya fue guardado en la base de datos."""
        return self.id is not None