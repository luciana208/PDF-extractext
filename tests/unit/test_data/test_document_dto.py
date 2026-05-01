"""
test_document_dto.py
--------------------
Tests unitarios para document_dto.py.
 
Qué se testea:
  - Que from_entity() mapea todos los campos correctamente.
  - Que to_entity() reconstruye la entidad sin pérdida de datos.
  - Que from_model() extrae los datos del modelo correctamente.
  - Que el DTO es inmutable (frozen=True).
"""
from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest

NOW = datetime(2024, 6, 15, 10, 30, tzinfo=timezone.utc)

def make_mock_entity(**kwargs):
    """Helper: crea una entidad mockeada con valores por defecto"""
    defaults = dict(
        id="64a1b2c3d4e5f6a7b8c9d0e1",
        name="documento.pdf",
        checksum="sha256abc",
        extracted_text="Contenido extraído",
        created_at=NOW,
        updated_at=NOW,
    )
    defaults.update(kwargs)
    e = MagicMock()
    for k, v in defaults.items():
        setattr(e, k, v)
    return e
 
 
def make_mock_model(**kwargs):
    defaults = dict(
        name="documento.pdf",
        checksum="sha256abc",
        extracted_text="Contenido extraído",
        created_at=NOW,
        updated_at=NOW,
    )
    defaults.update(kwargs)
    m = MagicMock()
    m.id.__str__ = lambda self: "64a1b2c3d4e5f6a7b8c9d0e1"
    for k, v in defaults.items():
        setattr(m, k, v)
    return m
 
 
class TestDocumentDTO:
    """Tests del DTO de transferencia entre capas."""
 
    def test_from_entity_mapea_todos_los_campos(self):
        """
        Dado: una entidad de dominio
        Cuando: creamos un DTO con from_entity()
        Entonces: todos los campos coinciden
        """
        from app.data.dto.document_dto import DocumentDTO
 
        entity = make_mock_entity()
        dto = DocumentDTO.from_entity(entity)
 
        assert dto.id == "64a1b2c3d4e5f6a7b8c9d0e1"
        assert dto.name == "documento.pdf"
        assert dto.checksum == "sha256abc"
        assert dto.extracted_text == "Contenido extraído"
        assert dto.created_at == NOW
 
    def test_dto_es_inmutable(self):
        """
        Dado: un DTO creado
        Cuando: intentamos modificar un campo
        Entonces: lanza FrozenInstanceError (frozen=True en dataclass)
        """
        from dataclasses import FrozenInstanceError
        from app.data.dto.document_dto import DocumentDTO
 
        dto = DocumentDTO(
            id="abc",
            name="file.pdf",
            checksum="xyz",
            extracted_text="",
            created_at=NOW,
            updated_at=NOW,
        )
 
        with pytest.raises(FrozenInstanceError):
            dto.name = "otro.pdf"  # Debe fallar
 
    def test_from_model_usa_str_del_id(self):
        """
        Dado: un modelo con id de tipo ObjectId (Mongo)
        Cuando: creamos un DTO con from_model()
        Entonces: el id se convierte a string
        """
        from app.data.dto.document_dto import DocumentDTO
 
        model = make_mock_model()
        dto = DocumentDTO.from_model(model)
 
        assert isinstance(dto.id, str)
        assert dto.name == "documento.pdf"
 
    def test_to_entity_reconstruye_datos(self):
        """
        Dado: un DTO con datos completos
        Cuando: llamamos a to_entity()
        Entonces: la entidad tiene los mismos datos (round-trip)
        """
        from app.data.dto.document_dto import DocumentDTO
 
        entity_original = make_mock_entity()
        dto = DocumentDTO.from_entity(entity_original)
 
        # to_entity() devuelve una entidad real de dominio
        entity_reconstruida = dto.to_entity()
 
        assert entity_reconstruida.name == entity_original.name
        assert entity_reconstruida.checksum == entity_original.checksum
        assert entity_reconstruida.extracted_text == entity_original.extracted_text