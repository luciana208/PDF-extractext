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
from app.business.services.document_service import DocumentService
from app.data.repositories.mongo_document_repository import MongoDocumentRepository


def get_document_service() -> DocumentService:
    return DocumentService(repository=MongoDocumentRepository())


def get_document_controller() -> DocumentController:
    return DocumentController(service=get_document_service())