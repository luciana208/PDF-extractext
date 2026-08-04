"""
document_router.py — Definición de los 5 endpoints HTTP
=========================================================
El Router es la "puerta de entrada" del sistema. Es el primer punto que recibe las peticiones HTTP del cliente y las dirige al Controller
correspondiente.

Responsabilidades del Router:
  - Declarar las rutas (URLs) y los métodos HTTP (POST, GET, PUT, DELETE).
  - Indicar los códigos de estado HTTP correctos para cada operación.
  - Extraer los parámetros de la request (path params, query params, body,
    archivos) y pasárselos al Controller.

Lo que el Router NO hace:
  - No valida lógica de negocio.
  - No accede a datos.
  - No contiene lógica de orquestación (eso es del Controller).

Principios aplicados:
  - SRP: solo define rutas y delega.
  - DRY: el Controller se inyecta una sola vez via Depends().
  - KISS: cada función del router es de 1-3 líneas; toda la lógica
    está en el Controller.
"""

from fastapi import APIRouter, Depends, File, Form, Query, Response, UploadFile, status

from app.dependencies import get_document_controller
from app.presentation.controllers.document_controller import DocumentController
from app.presentation.dto.request.update_request import UpdateRequestDTO
from app.presentation.dto.response.document_response import DocumentResponseDTO

# APIRouter agrupa todos los endpoints de documentos bajo el prefijo
# /api/v1/documents. El prefijo se registra en main.py al incluir este router.
router = APIRouter(
    prefix="/api/v1/documents",
    tags=["documents"],  # Agrupa los endpoints en la documentación Swagger.
)


@router.post(
    "/",
    response_model=DocumentResponseDTO,
    status_code=status.HTTP_201_CREATED,
    summary="Subir un documento PDF",
)
async def upload_document(
    file: UploadFile = File(..., description="Archivo PDF a subir."),
    custom_name: str | None = Form(default=None, description="Nombre opcional."),
    controller: DocumentController = Depends(get_document_controller),
) -> DocumentResponseDTO:
    """
    Sube un PDF al sistema.

    - Valida que sea un PDF real (magic bytes) y que no supere el tamaño máximo.
    - Extrae el texto del PDF y calcula su checksum SHA-256.
    - Detecta duplicados (mismo contenido = mismo checksum).
    - Persiste el documento y devuelve sus datos.
    """
    # Form fields llegan como parámetros separados en multipart/form-data;
    # los agrupamos en el DTO manualmente para mantener el contrato limpio.
    from app.presentation.dto.request.upload_request import UploadRequestDTO

    dto = UploadRequestDTO(custom_name=custom_name)
    return await controller.upload_document(file, dto)


@router.get(
    "/",
    response_model=list[DocumentResponseDTO],
    status_code=status.HTTP_200_OK,
    summary="Listar documentos (paginado)",
)
async def get_all_documents(
    skip: int = Query(0, ge=0, description="Documentos a saltar para paginación."),
    limit: int = Query(20, ge=1, le=100, description="Cantidad máxima de documentos por página (1-100)."),
    controller: DocumentController = Depends(get_document_controller),
) -> list[DocumentResponseDTO]:
    """
    Devuelve la lista paginada de documentos almacenados.
    
    - skip: cuántos documentos saltar (para navegar páginas).
    - limit: cuántos documentos traer por página (máx. 100).
    - Retorna una lista vacía si no hay documentos.
    """
    return await controller.get_all_documents(skip=skip, limit=limit)


@router.get(
    "/{document_id}/download",
    status_code=status.HTTP_200_OK,
    summary="Descargar el texto extraído como .txt",
)
async def download_document_text(
    document_id: str,
    controller: DocumentController = Depends(get_document_controller),
) -> Response:
    """Devuelve el texto extraído de un documento como archivo .txt."""
    return await controller.download_document_text(document_id)


@router.get(
    "/{document_id}",
    response_model=DocumentResponseDTO,
    status_code=status.HTTP_200_OK,
    summary="Obtener un documento por ID",
)
async def get_document_by_id(
    document_id: str,
    controller: DocumentController = Depends(get_document_controller),
) -> DocumentResponseDTO:
    """
    Busca y devuelve un documento por su ID único.
    Retorna 404 si el documento no existe.
    """
    return await controller.get_document_by_id(document_id)


@router.put(
    "/{document_id}",
    response_model=DocumentResponseDTO,
    status_code=status.HTTP_200_OK,
    summary="Actualizar metadatos de un documento",
)
async def update_document(
    document_id: str,
    dto: UpdateRequestDTO,
    controller: DocumentController = Depends(get_document_controller),
) -> DocumentResponseDTO:
    """
    Actualiza los metadatos de un documento existente (ej: custom_name).
    No permite modificar el contenido del PDF ni el checksum.
    Retorna 404 si el documento no existe.
    """
    return await controller.update_document(document_id, dto)


@router.delete(
    "/{document_id}",
    status_code=status.HTTP_200_OK,
    summary="Eliminar un documento",
)
async def delete_document(
    document_id: str,
    controller: DocumentController = Depends(get_document_controller),
) -> dict[str, str]:
    """
    Elimina un documento por su ID.
    Retorna 404 si el documento no existe.
    """
    return await controller.delete_document(document_id)