"""
test_mongo_connection.py
------------------------
Tests unitarios para mongo_connection.py.

Estrategia de testing (TDD aplicado):
  - Usamos mocks (unittest.mock) para NO necesitar un MongoDB real.
  - Testeamos la LÓGICA de la función (manejo de errores, Singleton, etc.),
    no si Mongo funciona (eso es responsabilidad de los tests de integración).

¿Por qué mockear?
  - Los tests unitarios deben ser rápidos y no depender de servicios externos.
  - Con mocks controlamos exactamente qué devuelve el driver, incluyendo errores.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

# Importamos el módulo completo para poder resetear sus variables globales entre tests
import app.data.database.mongo_connection as conn_module


@pytest.fixture(autouse=True)
def reset_connection_state():
    """
    Fixture que resetea el estado del módulo antes de cada test.
    Como _client y _database son variables de módulo (Singleton), si un test
    las modifica afecta al siguiente. autouse=True las limpia automáticamente.
    """
    conn_module._client = None
    conn_module._database = None
    yield
    conn_module._client = None
    conn_module._database = None


class TestConnect:
    """Tests para la función connect()."""

    @pytest.mark.asyncio
    async def test_connect_exitoso(self):
        """
        Dado: una URL de Mongo válida en settings
        Cuando: llamamos a connect()
        Entonces: _client y _database quedan inicializados
        """
        mock_client = MagicMock()
        mock_client.server_info = AsyncMock(return_value={"version": "6.0"})
        mock_client.__getitem__ = MagicMock(return_value=MagicMock())

        with patch("app.data.database.mongo_connection.motor.motor_asyncio.AsyncIOMotorClient",
                   return_value=mock_client):
            with patch("app.data.database.mongo_connection.settings") as mock_settings:
                mock_settings.MONGO_URL = "mongodb://localhost:27017"
                mock_settings.DB_NAME = "test_db"

                await conn_module.connect()

        assert conn_module._client is not None
        assert conn_module._database is not None

    @pytest.mark.asyncio
    async def test_connect_falla_si_url_invalida(self):
        """
        Dado: una URL de Mongo inaccesible
        Cuando: llamamos a connect()
        Entonces: se lanza una excepción (no arranca la app rota)
        """
        from pymongo.errors import ConnectionFailure

        mock_client = MagicMock()
        mock_client.server_info = AsyncMock(side_effect=ConnectionFailure("Sin conexión"))

        with patch("app.data.database.mongo_connection.motor.motor_asyncio.AsyncIOMotorClient",
                   return_value=mock_client):
            with patch("app.data.database.mongo_connection.settings") as mock_settings:
                mock_settings.MONGO_URL = "mongodb://url-inexistente:27017"
                mock_settings.DB_NAME = "test_db"

                with pytest.raises(ConnectionFailure):
                    await conn_module.connect()


class TestDisconnect:
    """Tests para la función disconnect()."""

    @pytest.mark.asyncio
    async def test_disconnect_cierra_cliente(self):
        """
        Dado: un cliente activo
        Cuando: llamamos a disconnect()
        Entonces: se llama a client.close() y _client vuelve a None
        """
        mock_client = MagicMock()
        conn_module._client = mock_client

        await conn_module.disconnect()

        mock_client.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_disconnect_sin_cliente_no_falla(self):
        """
        Dado: ningún cliente activo (_client = None)
        Cuando: llamamos a disconnect()
        Entonces: no lanza excepción (idempotente)
        """
        conn_module._client = None
        # No debe lanzar excepción
        await conn_module.disconnect()


class TestGetDatabase:
    """Tests para la función get_database()."""

    def test_get_database_retorna_db_inicializada(self):
        """
        Dado: una DB inicializada
        Cuando: llamamos a get_database()
        Entonces: retorna el objeto de base de datos
        """
        mock_db = MagicMock()
        conn_module._database = mock_db

        result = conn_module.get_database()

        assert result is mock_db

    def test_get_database_lanza_error_si_no_conectado(self):
        """
        Dado: _database = None (connect() no fue llamado)
        Cuando: llamamos a get_database()
        Entonces: se lanza RuntimeError con mensaje descriptivo
        """
        conn_module._database = None

        with pytest.raises(RuntimeError, match="no está inicializada"):
            conn_module.get_database()