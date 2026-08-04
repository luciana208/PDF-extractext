"""
dependencies.py — Inyección de dependencias
============================================
FastAPI usa el patrón Dependency Injection (DI) a través de Depends(). Este archivo centraliza la construcción de los objetos que se inyectan
en los endpoints.

¿Por qué es importante este archivo?
  - DIP (SOLID): el Router y el Controller nunca crean sus dependencias; las reciben desde afuera. Esto permite cambiar implementaciones sin
    tocar el código de los consumers.
  - Testabilidad: en los tests se puede sobreescribir estas funciones para inyectar mocks en lugar de implementaciones reales.
  - DRY: la construcción del Controller ocurre en un solo lugar.
"""




from app.presentation.controllers.document_controller import DocumentController
from app.data.repositories.mongo_document_repository import MongoDocumentRepository
from app.use_cases.process_pdf import ProcessPDFUseCase
from app.use_cases.list_documents import ListDocumentsUseCase
from app.use_cases.get_document import GetDocumentUseCase
from app.use_cases.update_document import UpdateDocumentUseCase
from app.use_cases.delete_document import DeleteDocumentUseCase
from app.use_cases.download_text import DownloadTextUseCase


def get_document_controller() -> DocumentController:
  repo = MongoDocumentRepository()
  return DocumentController(
    process_pdf=ProcessPDFUseCase(repo),
    list_documents=ListDocumentsUseCase(repo),
    get_document=GetDocumentUseCase(repo),
    update_document=UpdateDocumentUseCase(repo),
    delete_document=DeleteDocumentUseCase(repo),
    download_text=DownloadTextUseCase(repo),
  )