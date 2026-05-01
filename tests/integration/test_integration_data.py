"""
test_integration_data.py
-------------------------
Tests de INTEGRACIÓN para la capa de Datos.
...
"""

import pytest
from datetime import datetime, timezone
import os

pytestmark = pytest.mark.integration


@pytest.fixture(scope="function")  # ← cambiado de "module" a "function"
async def db_connection():
    from app.data.database.mongo_connection import connect, disconnect
    from beanie import init_beanie
    from app.data.models.document_model import DocumentModel
    from app.data.database.mongo_connection import get_database

    os.environ.setdefault("MONGO_URL", "mongodb://localhost:27017")
    os.environ.setdefault("DB_NAME", "test_pdf_extractext")

    await connect()
    await init_beanie(database=get_database(), document_models=[DocumentModel])
    yield
    await disconnect()


@pytest.fixture(autouse=True)
async def limpiar_coleccion(db_connection):
    from app.data.models.document_model import DocumentModel
    await DocumentModel.find_all().delete()
    yield
    await DocumentModel.find_all().delete()


def make_test_entity(filename="test.pdf", checksum="abc123def456", extracted_text="Texto de prueba"):
    from app.business.entities.document import Document
    return Document(
        filename=filename,
        checksum=checksum,
        extracted_text=extracted_text,
    )


class TestIntegrationRepository:

    @pytest.mark.asyncio
    async def test_save_y_get_by_id(self):
        from app.data.repositories.mongo_document_repository import MongoDocumentRepository

        repo = MongoDocumentRepository()
        entity = make_test_entity(filename="integración.pdf")

        guardado = await repo.save(entity)
        assert guardado.id is not None

        recuperado = await repo.get_by_id(guardado.id)
        assert recuperado is not None
        assert recuperado.filename == "integración.pdf"  # ← era .name
        assert recuperado.checksum == entity.checksum

    @pytest.mark.asyncio
    async def test_get_all_retorna_todos(self):
        from app.data.repositories.mongo_document_repository import MongoDocumentRepository

        repo = MongoDocumentRepository()
        for i in range(3):
            await repo.save(make_test_entity(filename=f"doc{i}.pdf", checksum=f"checksum{i}"))

        todos = await repo.get_all()
        assert len(todos) == 3

    @pytest.mark.asyncio
    async def test_delete_elimina_de_la_bd(self):
        from app.data.repositories.mongo_document_repository import MongoDocumentRepository

        repo = MongoDocumentRepository()
        guardado = await repo.save(make_test_entity())

        eliminado = await repo.delete(guardado.id)
        assert eliminado is True

        no_existe = await repo.get_by_id(guardado.id)
        assert no_existe is None

    @pytest.mark.asyncio
    async def test_checksum_duplicado_lanza_error(self):
        from app.data.repositories.mongo_document_repository import MongoDocumentRepository

        repo = MongoDocumentRepository()
        await repo.save(make_test_entity(checksum="checksum_unico"))

        with pytest.raises(ValueError, match="checksum"):
            await repo.save(make_test_entity(filename="copia.pdf", checksum="checksum_unico"))  # ← era name=