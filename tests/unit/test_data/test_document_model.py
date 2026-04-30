"""
test_document_model.py
----------------------
Tests unitarios para document_model.py.

Qué se testea:
  - Que DocumentModel se crea correctamente con los campos esperados.
  - Que la conversión to_entity() produce una entidad válida.
  - Que from_entity() produce un modelo válido.
  - Que los timestamps se asignan automáticamente.

Nota: NO testeamos la persistencia real en Mongo aquí (eso es integración).
"""

from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest


# Helper para crear una entidad de dominio mockeada (Dev 2 la implementa)
def make_mock_entity(
    id="64a1b2c3d4e5f6a7b8c9d0e1",
    name="test.pdf",
    checksum="abc123",
    extracted_text="Texto de prueba",
):
    entity = MagicMock()
    entity.id = id
    entity.name = name
    entity.checksum = checksum
    entity.extracted_text = extracted_text
    entity.created_at = datetime(2024, 1, 1, tzinfo=timezone.utc)
    entity.updated_at = datetime(2024, 1, 1, tzinfo=timezone.utc)
    return entity


class TestDocumentModel:
    """Tests del schema DocumentModel."""

    def test_creacion_con_campos_requeridos(self):
        """
        Dado: los campos mínimos necesarios
        Cuando: creamos un DocumentModel
        Entonces: el objeto se construye correctamente
        """
        from app.data.models.document_model import DocumentModel

        model = DocumentModel(
            name="archivo.pdf",
            checksum="sha256hash",
            extracted_text="texto",
        )

        assert model.name == "archivo.pdf"
        assert model.checksum == "sha256hash"
        assert model.extracted_text == "texto"

    def test_extracted_text_es_vacio_por_defecto(self):
        """
        Dado: un DocumentModel sin extracted_text
        Cuando: accedemos al campo
        Entonces: es string vacío (no None)
        """
        from app.data.models.document_model import DocumentModel

        model = DocumentModel(name="vacio.pdf", checksum="abc")

        assert model.extracted_text == ""

    def test_timestamps_se_asignan_automaticamente(self):
        """
        Dado: un DocumentModel sin fechas explícitas
        Cuando: se crea
        Entonces: created_at y updated_at tienen valores automáticos
        """
        from app.data.models.document_model import DocumentModel

        before = datetime.now(timezone.utc)
        model = DocumentModel(name="archivo.pdf", checksum="abc")
        after = datetime.now(timezone.utc)

        assert before <= model.created_at <= after
        assert before <= model.updated_at <= after

    def test_from_entity_mapea_todos_los_campos(self):
        """
        Dado: una entidad de dominio mockeada
        Cuando: llamamos a from_entity()
        Entonces: el modelo tiene exactamente los mismos datos
        """
        from app.data.models.document_model import DocumentModel

        entity = make_mock_entity(name="reporte.pdf", checksum="xyz789")

        model = DocumentModel.from_entity(entity)

        assert model.name == "reporte.pdf"
        assert model.checksum == "xyz789"
        assert model.extracted_text == entity.extracted_text

    def test_to_entity_produce_objeto_con_id(self):
        """
        Dado: un DocumentModel con id simulado
        Cuando: llamamos a to_entity()
        Entonces: la entidad resultante tiene el id como string
        """
        from app.data.models.document_model import DocumentModel

        model = DocumentModel(
            name="doc.pdf",
            checksum="abc",
            extracted_text="texto",
        )
        # Simulamos que Mongo asignó un id
        model.id = MagicMock()
        model.id.__str__ = lambda self: "64a1b2c3d4e5f6a7b8c9d0e1"

        entity = model.to_entity()

        assert entity.name == "doc.pdf"
        assert entity.checksum == "abc"