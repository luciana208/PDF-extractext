"""
document_controller.py — Controlador de documentos
====================================================
El Controller es el "director de orquesta" de la capa de Presentación.
Su trabajo es:
  1. Recibir los datos ya validados del router.
  2. Llamar al Service (capa de Negocio) con esos datos.
  3. Construir y devolver la respuesta apropiada al cliente.

Lo que el Controller NO hace:
  - No valida lógica de negocio (eso es del Service).
  - No accede a la base de datos (eso es de la capa de Datos).
  - No construye la respuesta con datos crudos de MongoDB.

Principios aplicados:
  - SRP: orquesta, no implementa lógica.
  - DIP (SOLID): depende de la INTERFAZ IDocumentService, no de la
    implementación concreta. Esto permite testear con mocks fácilmente.
  - KISS: cada método del controller tiene un propósito claro y corto.
"""

from fastapi import HTTPException, UploadFile, status

from app.business.services.interfaces.i_document_service import IDocumentService
from app.presentation.dto.request.update_request import UpdateRequestDTO
from app.presentation.dto.request.upload_request import UploadRequestDTO
from app.presentation.dto.response.document_response import DocumentResponseDTO
from app.presentation.validators.pdf_validator import validate_pdf


class DocumentController:
    """
    Orquesta las operaciones CRUD sobre documentos PDF.

    Recibe una instancia de IDocumentService en el constructor (inyección de dependencias). Nunca instancia el Service directamente: eso
    permite reemplazarlo por un mock en los tests sin cambiar este código.
    """

    def __init__(self, service: IDocumentService) -> None:
        """
        Args:
            service: Implementación del servicio de documentos.
                     Inyectada desde dependencies.py vía FastAPI.
        """
        self._service = service

    # ------------------------------------------------------------------ #
    # UPLOAD — POST /api/v1/documents                                      #
    # ------------------------------------------------------------------ #

    async def upload_document(
        self,
        file: UploadFile,
        dto: UploadRequestDTO,
    ) -> DocumentResponseDTO:
        """
        Procesa la subida de un PDF:
          1. Valida formato y tamaño del archivo.
          2. Delega el procesamiento (extracción, checksum, guardado) al Service.
          3. Devuelve el documento creado.

        Args:
            file: Archivo PDF recibido en el multipart/form-data.
            dto:  Metadatos opcionales (custom_name).

        Returns:
            DocumentResponseDTO con los datos del documento creado.

        Raises:
            HTTPException 400/413: Si la validación del PDF falla.
            HTTPException 409: Si ya existe un documento con el mismo contenido.
        """
        # La validación de formato/tamaño es responsabilidad de Presentación.
        await validate_pdf(file)

        # El Service hace el trabajo pesado: checksum, extracción de texto,
        # detección de duplicados y persistencia.
        result = await self._service.process_document(file, dto)
        return result

    # ------------------------------------------------------------------ #
    # GET ALL — GET /api/v1/documents                                      #
    # ------------------------------------------------------------------ #

    async def get_all_documents(self) -> list[DocumentResponseDTO]:
        """
        Obtiene la lista completa de documentos almacenados.

        Returns:
            Lista de DocumentResponseDTO (puede ser vacía).
        """
        return await self._service.get_all()

    # ------------------------------------------------------------------ #
    # GET ONE — GET /api/v1/documents/{document_id}                        #
    # ------------------------------------------------------------------ #

    async def get_document_by_id(self, document_id: str) -> DocumentResponseDTO:
        """
        Busca un documento por su ID.

        Args:
            document_id: ID del documento (ObjectId de MongoDB como string).

        Returns:
            DocumentResponseDTO si se encuentra.

        Raises:
            HTTPException 404: Si no existe ningún documento con ese ID.
        """
        result = await self._service.get_by_id(document_id)
        if result is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Documento con id '{document_id}' no encontrado.",
            )
        return result

    # ------------------------------------------------------------------ #
    # UPDATE — PUT /api/v1/documents/{document_id}                         #
    # ------------------------------------------------------------------ #

    async def update_document(
        self,
        document_id: str,
        dto: UpdateRequestDTO,
    ) -> DocumentResponseDTO:
        """
        Actualiza los metadatos de un documento existente.

        Args:
            document_id: ID del documento a actualizar.
            dto:         Campos a modificar (solo metadatos).

        Returns:
            DocumentResponseDTO con los datos actualizados.

        Raises:
            HTTPException 404: Si el documento no existe.
        """
        result = await self._service.update(document_id, dto)
        if result is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Documento con id '{document_id}' no encontrado.",
            )
        return result

    # ------------------------------------------------------------------ #
    # DELETE — DELETE /api/v1/documents/{document_id}                      #
    # ------------------------------------------------------------------ #

    async def delete_document(self, document_id: str) -> dict[str, str]:
        """
        Elimina un documento por su ID.

        Args:
            document_id: ID del documento a eliminar.

        Returns:
            Diccionario con mensaje de confirmación.

        Raises:
            HTTPException 404: Si el documento no existe.
        """
        deleted = await self._service.delete(document_id)
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Documento con id '{document_id}' no encontrado.",
            )
        return {"message": f"Documento '{document_id}' eliminado correctamente."}