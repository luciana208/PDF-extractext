"""
test_integration_data.py
-------------------------
Tests de INTEGRACIÓN para la capa de Datos.

A diferencia de los tests unitarios (que usan mocks), estos tests
se conectan a un MongoDB REAL (local o Docker) y verifican que
las operaciones de persistencia funcionen de verdad.

Cómo correr solo estos tests:
  pytest tests/integration/ -v

Cómo correr con MongoDB en Docker (sin instalar MongoDB localmente):
  docker run -d -p 27017:27017 mongo:6
  pytest tests/integration/ -v

Nota: estos tests se marcan con @pytest.mark.integration para poder
excluirlos en CI si no hay MongoDB disponible:
  pytest -m "not integration"
"""

import pytest
from datetime import datetime, timezone


pytestmark = pytest.mark.integration  # Marca todos los tests de este archivo


@pytest.fixture(scope="module")
async def db_connection():
    """
    Fixture de módulo: conecta a MongoDB UNA sola vez para todos los tests.
    Al terminar, desconecta. scope="module" evita reconectar en cada test.
    """
    from app.data.database.mongo_connection import connect, disconnect

    # Usamos una DB de prueba para no contaminar la DB de producción
    import os
    os.environ.setdefault("MONGO_URL", "mongodb://localhost:27017")
    os.environ.setdefault("DB_NAME", "test_pdf_extractext")

    await connect()
    yield
    await disconnect()


@pytest.fixture(autouse=True)
async def limpiar_coleccion(db_connection):
    """
    Limpia la colección antes de cada test para que sean independientes.
    autouse=True la aplica a todos los tests del archivo.
    """
    from app.data.models.document_model import DocumentModel
    await DocumentModel.find_all().delete()
    yield
    # Limpieza también después del test
    await DocumentModel.find_all().delete()


def make_test_entity(name="test.pdf", checksum="abc123def456", extracted_text="Texto de prueba"):
    """Helper: crea entidad de prueba real (no mock)."""
    from app.business.entities.document import Document
    return Document(
        id=None,
        name=name,
        checksum=checksum,
        extracted_text=extracted_text,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )


class TestIntegrationRepository:
    """
    Tests de integración del repositorio completo.
    Verifican el flujo real: Python → Beanie → MongoDB → Python.
    """

    @pytest.mark.asyncio
    async def test_save_y_get_by_id(self):
        """
        Dado: una entidad válida
        Cuando: guardamos y luego buscamos por id
        Entonces: recuperamos exactamente lo que guardamos
        """
        from app.data.repositories.mongo_document_repository import MongoDocumentRepository

        repo = MongoDocumentRepository()
        entity = make_test_entity(name="integración.pdf")

        guardado = await repo.save(entity)
        assert guardado.id is not None

        recuperado = await repo.get_by_id(guardado.id)
        assert recuperado is not None
        assert recuperado.name == "integración.pdf"
        assert recuperado.checksum == entity.checksum

    @pytest.mark.asyncio
    async def test_get_all_retorna_todos(self):
        """
        Dado: 3 documentos guardados
        Cuando: llamamos a get_all()
        Entonces: retorna exactamente 3 documentos
        """
        from app.data.repositories.mongo_document_repository import MongoDocumentRepository

        repo = MongoDocumentRepository()
        for i in range(3):
            await repo.save(make_test_entity(name=f"doc{i}.pdf", checksum=f"checksum{i}"))

        todos = await repo.get_all()
        assert len(todos) == 3

    @pytest.mark.asyncio
    async def test_delete_elimina_de_la_bd(self):
        """
        Dado: un documento guardado
        Cuando: lo eliminamos
        Entonces: ya no existe en la BD
        """
        from app.data.repositories.mongo_document_repository import MongoDocumentRepository

        repo = MongoDocumentRepository()
        guardado = await repo.save(make_test_entity())

        eliminado = await repo.delete(guardado.id)
        assert eliminado is True

        no_existe = await repo.get_by_id(guardado.id)
        assert no_existe is None

    @pytest.mark.asyncio
    async def test_checksum_duplicado_lanza_error(self):
        """
        Dado: un documento con checksum X ya guardado
        Cuando: guardamos otro con el mismo checksum X
        Entonces: lanza ValueError (duplicado detectado)
        """
        from app.data.repositories.mongo_document_repository import MongoDocumentRepository

        repo = MongoDocumentRepository()
        await repo.save(make_test_entity(checksum="checksum_unico"))

        with pytest.raises(ValueError, match="checksum"):
            await repo.save(make_test_entity(name="copia.pdf", checksum="checksum_unico"))