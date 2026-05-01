"""
mongo_conection.py
------------------
Responsabilidad ÚNICA (SOLID - S): gestionar la conexión a MongoDB.
Nadie más en el proyecto abre ni cierra la base de datos.

¿Qué hace este archivo?
    - Lee la URL de MongoDB desde las variables de entorno (12-Farctor App).
    - Crea UN SOLO cliente Motor (patrón Singleton implícito via variable de módulo).
    - Expone dos funciones: connect() y disconnect(), llamadas desde main.py en los eventos de startup/shutdown de FastAPI.
    - Expone get_database() para que los repositorios obtengan la DB sin
    saber cómo se conecta.

Motor es el driver async de MongoDB para Python. Usa asyncio internamente, 
por eso todas las operaciones son `await`.
"""
import logging

import motor.motor_asyncio
from pymongo.errors import ConnectionFailure, ConfigurationError
 
from app.config.settings import settings # Lee MONGO_URL, DB_NAME desde .env
 
# Logger propio del módulo (KISS: no configuramos nada extra aquí)
logger = logging.getLogger(__name__)
 
# Variable de módulo que guarda el cliente. Al ser variable de módulo,
# se comparte entre todas las importaciones → efecto Singleton.
_client: motor.motor_asyncio.AsyncIOMotorClient | None = None
_database: motor.motor_asyncio.AsyncIOMotorDatabase | None = None
 
 
async def connect() -> None:
    """
    Abre la conexión a MongoDB.
    FastAPI llama a esta función en el evento 'startup' (ver main.py).
 
    Motor no conecta realmente hasta que se hace la primera operación,
    pero server_info() fuerza el handshake para verificar que la URL es válida.
    Si la URL es incorrecta, falla aquí con un mensaje claro.
    """
    global _client, _database
 
    try:
        _client = motor.motor_asyncio.AsyncIOMotorClient(
            settings.MONGO_URL,
            serverSelectionTimeoutMS=5000,  # Falla rápido si no hay servidor
        )
        # Forzar handshake para detectar errores de conexión al arrancar
        await _client.server_info()
        _database = _client[settings.DB_NAME]
        logger.info("Conexión a MongoDB establecida: %s / %s", settings.MONGO_URL, settings.DB_NAME)
 
    except (ConnectionFailure, ConfigurationError) as exc:
        # Re-lanzamos para que FastAPI no arranque con la DB rota
        logger.error("No se pudo conectar a MongoDB: %s", exc)
        raise
 
 
async def disconnect() -> None:
    """
    Cierra la conexión a MongoDB.
    FastAPI llama a esta función en el evento 'shutdown' (ver main.py).
    """
    global _client
    if _client:
        _client.close()
        logger.info("Conexión a MongoDB cerrada.")
 
 
def get_database() -> motor.motor_asyncio.AsyncIOMotorDatabase:
    """
    Retorna la instancia de la base de datos.
    Los repositorios llaman a esta función para obtener la DB.
 
    Raises:
        RuntimeError: si se llama antes de connect() (no debería pasar en producción).
    """
    if _database is None:
        raise RuntimeError("La base de datos no está inicializada. ¿Llamaste a connect()?")
    return _database