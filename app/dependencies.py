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

Nota: En la integración final, get_document_service() será provisto por Dev 2 (Business Layer). Por ahora se deja como stub para que
Dev 1 pueda desarrollar y testear independientemente.
"""

from app.presentation.controllers.document_controller import DocumentController

# STUB temporal: se reemplazará con la implementación real de Dev 2 cuando se integren las capas. No borrar el comentario; sirve de
# recordatorio para el momento de integración.
def get_document_service():
    """
    Retorna la implementación del servicio de documentos.

    En integración: importar DocumentService desde business.services y retornar una instancia conectada al repositorio de Dev 3.
    """
    # TODO (integración): from app.business.services.document_service import DocumentService
    # TODO (integración): from app.data.repositories.mongo_document_repository import MongoDocumentRepository
    # TODO (integración): return DocumentService(repository=MongoDocumentRepository())
    raise NotImplementedError(
        "El DocumentService aún no está integrado. "
        "En tests, sobreescribir app.dependencies.get_document_service."
    )


def get_document_controller(
    service=None,  # FastAPI lo resolverá via Depends en la integración real
) -> DocumentController:
    """
    Construye y devuelve el DocumentController con su Service inyectado.

    En los tests de integración se puede sobreescribir esta función para inyectar un Service mockeado.
    """
    if service is None:
        service = get_document_service()
    return DocumentController(service=service)