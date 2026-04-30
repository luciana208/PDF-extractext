from fastapi import FastAPI
from app.presentation.routers.document_router import router as document_router

app = FastAPI()

# Registrar el router de documentos
app.include_router(document_router)