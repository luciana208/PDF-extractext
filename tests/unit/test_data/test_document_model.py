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
from beanie.odm.documents import DocumentSettings
#Importamos aquí para que esté disponible en todos los tests
from app.data.models.document_model import DocumentModel

def make_mock_entity(**kwargs):
    """Función auxiliar para crear entidades de dominio simuladas"""
    entity = MagicMock()
    # CAMBIO: Usar 'filename' en lugar de 'file_name' para coincidir con la entidad
    entity.filename = kwargs.get("name", "test.pdf") 
    entity.checksum = kwargs.get("checksum", "abc123")
    entity.extracted_text = kwargs.get("extracted_text", "Texto de prueba")
    entity.id = kwargs.get("id", "64a1b2c3d4e5f6a7b8c9d0e1")
    entity.created_at = datetime(2024, 1, 1, tzinfo=timezone.utc)
    entity.updated_at = datetime(2024, 1, 1, tzinfo=timezone.utc)
    return entity

class TestDocumentModel:
    
    """Tests del schema DocumentModel."""

    @pytest.fixture(autouse=True)
    def mock_beanie_settings(self):
        """Inyecta una configuración falsa para que Beanie no pida DB real"""
        # Esto evita el error CollectionWasNotInitialized
        DocumentModel._document_settings = DocumentSettings(
            name="documents",
            model_type=DocumentModel
        )
        
    

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
      
    def test_extracted_text_es_vacio_por_defecto(self):
        """
        Dado: un DocumentModel sin extracted_text
        Cuando: accedemos al campo
        Entonces: es string vacío (no None)
        """
        model = DocumentModel(name="vacio.pdf", checksum="abc")
        assert model.extracted_text == ""

    def test_timestamps_se_asignan_automaticamente(self):
        """
        Dado: un DocumentModel sin fechas explícitas
        Cuando: se crea
        Entonces: created_at y updated_at tienen valores automáticos
        """

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
        entity = make_mock_entity(name="reporte.pdf", checksum="xyz789")
        model = DocumentModel.from_entity(entity)

        assert model.name == "reporte.pdf"
        assert model.checksum == "xyz789"

    def test_to_entity_produce_objeto_con_id(self):
        """
        Dado: un DocumentModel con id simulado
        Cuando: llamamos a to_entity()
        Entonces: la entidad resultante tiene el id como string
        """
        model = DocumentModel(name="doc.pdf", checksum="abc")
        model.id = "64a1b2c3d4e5f6a7b8c9d0e1"

        entity = model.to_entity()

        # CAMBIO: La entidad usa 'filename', no 'file_name'[cite: 1]
        assert entity.filename == "doc.pdf" 
        assert str(entity.id) == "64a1b2c3d4e5f6a7b8c9d0e1"