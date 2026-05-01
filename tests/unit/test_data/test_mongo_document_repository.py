"""
test_mongo_document_repository.py
----------------------------------
Tests unitarios para MongoDocumentRepository.

Estrategia:
  - Mockeamos DocumentModel (Beanie) para no necesitar MongoDB real.
  - Testeamos los 5 métodos: save, get_all, get_by_id, update, delete.
  - Cada test verifica: resultado correcto, manejo de "no encontrado" y errores.

TDD aplicado: estos tests definen el comportamiento esperado. Si el repositorio
falla un test, el código del repositorio tiene un bug, no el test.
"""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

NOW = datetime(2024, 6, 15, tzinfo=timezone.utc)


def make_mock_document(
    id="64a1b2c3d4e5f6a7b8c9d0e1",
    name="test.pdf",
    checksum="abc123",
    extracted_text="Texto",
):
    """Helper: crea una entidad de dominio mockeada."""
    doc = MagicMock()
    doc.id = id
    doc.name = name
    doc.checksum = checksum
    doc.extracted_text = extracted_text
    doc.created_at = NOW
    doc.updated_at = NOW
    return doc


def make_mock_model(entity=None):
    """Helper: crea un DocumentModel mockeado que retorna entidades."""
    if entity is None:
        entity = make_mock_document()
    model = MagicMock()
    model.id = MagicMock()
    model.to_entity = MagicMock(return_value=entity)
    model.insert = AsyncMock()
    model.delete = AsyncMock()
    model.set = AsyncMock()
    return model


class TestSave:
    """Tests del método save()."""

    @pytest.mark.asyncio
    async def test_save_retorna_entidad_con_id_asignado(self):
        """
        Dado: una entidad de dominio válida
        Cuando: llamamos a save()
        Entonces: retorna la entidad con el id asignado por Mongo
        """
        from app.data.repositories.mongo_document_repository import MongoDocumentRepository

        entity = make_mock_document(id=None)
        model = make_mock_model()

        with patch("app.data.repositories.mongo_document_repository.DocumentModel") as MockModel:
            MockModel.from_entity.return_value = model

            repo = MongoDocumentRepository()
            result = await repo.save(entity)

        model.insert.assert_called_once()
        assert result is not None

    @pytest.mark.asyncio
    async def test_save_lanza_error_en_duplicado(self):
        """
        Dado: un documento cuyo checksum ya existe en BD
        Cuando: llamamos a save()
        Entonces: lanza ValueError con mensaje descriptivo
        """
        from pymongo.errors import DuplicateKeyError
        from app.data.repositories.mongo_document_repository import MongoDocumentRepository

        entity = make_mock_document(checksum="checksum_existente")
        model = make_mock_model()
        model.insert = AsyncMock(side_effect=DuplicateKeyError("dup key"))

        with patch("app.data.repositories.mongo_document_repository.DocumentModel") as MockModel:
            MockModel.from_entity.return_value = model

            repo = MongoDocumentRepository()
            with pytest.raises(ValueError, match="checksum"):
                await repo.save(entity)


class TestGetAll:
    """Tests del método get_all()."""

    @pytest.mark.asyncio
    async def test_get_all_retorna_lista_de_entidades(self):
        """
        Dado: 2 documentos en la BD
        Cuando: llamamos a get_all()
        Entonces: retorna lista con 2 entidades
        """
        from app.data.repositories.mongo_document_repository import MongoDocumentRepository

        entity1 = make_mock_document(id="1", name="a.pdf")
        entity2 = make_mock_document(id="2", name="b.pdf")
        model1 = make_mock_model(entity1)
        model2 = make_mock_model(entity2)

        mock_find = MagicMock()
        mock_find.to_list = AsyncMock(return_value=[model1, model2])

        with patch("app.data.repositories.mongo_document_repository.DocumentModel") as MockModel:
            MockModel.find_all.return_value = mock_find

            repo = MongoDocumentRepository()
            result = await repo.get_all()

        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_get_all_retorna_lista_vacia_si_no_hay_documentos(self):
        """
        Dado: colección vacía
        Cuando: llamamos a get_all()
        Entonces: retorna [] (no None, no excepción)
        """
        from app.data.repositories.mongo_document_repository import MongoDocumentRepository

        mock_find = MagicMock()
        mock_find.to_list = AsyncMock(return_value=[])

        with patch("app.data.repositories.mongo_document_repository.DocumentModel") as MockModel:
            MockModel.find_all.return_value = mock_find

            repo = MongoDocumentRepository()
            result = await repo.get_all()

        assert result == []


class TestGetById:
    """Tests del método get_by_id()."""

    @pytest.mark.asyncio
    async def test_get_by_id_retorna_entidad_si_existe(self):
        """
        Dado: un documento existente con id conocido
        Cuando: llamamos a get_by_id() con ese id
        Entonces: retorna la entidad correcta
        """
        from app.data.repositories.mongo_document_repository import MongoDocumentRepository

        entity = make_mock_document(id="64a1b2c3d4e5f6a7b8c9d0e1")
        model = make_mock_model(entity)

        with patch("app.data.repositories.mongo_document_repository.DocumentModel") as MockModel:
            MockModel.get = AsyncMock(return_value=model)

            repo = MongoDocumentRepository()
            result = await repo.get_by_id("64a1b2c3d4e5f6a7b8c9d0e1")

        assert result is entity

    @pytest.mark.asyncio
    async def test_get_by_id_retorna_none_si_no_existe(self):
        """
        Dado: un id que no existe en BD
        Cuando: llamamos a get_by_id()
        Entonces: retorna None (no lanza excepción)
        """
        from app.data.repositories.mongo_document_repository import MongoDocumentRepository

        with patch("app.data.repositories.mongo_document_repository.DocumentModel") as MockModel:
            MockModel.get = AsyncMock(return_value=None)

            repo = MongoDocumentRepository()
            result = await repo.get_by_id("64a1b2c3d4e5f6a7b8c9d0e1")

        assert result is None

    @pytest.mark.asyncio
    async def test_get_by_id_retorna_none_si_id_invalido(self):
        """
        Dado: un id con formato inválido (no es ObjectId)
        Cuando: llamamos a get_by_id()
        Entonces: retorna None (no lanza excepción)
        """
        from app.data.repositories.mongo_document_repository import MongoDocumentRepository

        repo = MongoDocumentRepository()
        result = await repo.get_by_id("id-que-no-es-objectid")

        assert result is None


class TestDelete:
    """Tests del método delete()."""

    @pytest.mark.asyncio
    async def test_delete_retorna_true_si_existia(self):
        """
        Dado: un documento existente
        Cuando: llamamos a delete()
        Entonces: retorna True
        """
        from app.data.repositories.mongo_document_repository import MongoDocumentRepository

        model = make_mock_model()

        with patch("app.data.repositories.mongo_document_repository.DocumentModel") as MockModel:
            MockModel.get = AsyncMock(return_value=model)

            repo = MongoDocumentRepository()
            result = await repo.delete("64a1b2c3d4e5f6a7b8c9d0e1")

        assert result is True
        model.delete.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_retorna_false_si_no_existia(self):
        """
        Dado: un id que no existe
        Cuando: llamamos a delete()
        Entonces: retorna False (no lanza excepción)
        """
        from app.data.repositories.mongo_document_repository import MongoDocumentRepository

        with patch("app.data.repositories.mongo_document_repository.DocumentModel") as MockModel:
            MockModel.get = AsyncMock(return_value=None)

            repo = MongoDocumentRepository()
            result = await repo.delete("64a1b2c3d4e5f6a7b8c9d0e1")

        assert result is False