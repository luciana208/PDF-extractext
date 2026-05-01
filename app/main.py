from fastapi import FastAPI
from beanie import init_beanie

from app.data.database.mongo_connection import connect, disconnect, get_database
from app.data.models.document_model import DocumentModel
from app.presentation.routers.document_router import router as document_router

app = FastAPI()

# Registrar el router de documentos
app.include_router(document_router)


@app.on_event("startup")
async def startup():
    # Conectar a MongoDB
    await connect()
    
    # Inicializar Beanie con los modelos
    await init_beanie(
        database=get_database(),
        document_models=[DocumentModel],
    )


@app.on_event("shutdown")
async def shutdown():
    # Cerrar conexión a MongoDB
    await disconnect()