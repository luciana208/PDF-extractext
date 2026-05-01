from fastapi import HTTPException, UploadFile, status

from app.business.domain.exceptions import DocumentNotFoundError, DuplicateDocumentError
from app.business.services.interfaces.i_document_service import IDocumentService
from app.presentation.dto.request.update_request import UpdateRequestDTO
from app.presentation.dto.request.upload_request import UploadRequestDTO
from app.presentation.dto.response.document_response import DocumentResponseDTO
from app.presentation.validators.pdf_validator import validate_pdf


class DocumentController:

    def __init__(self, service: IDocumentService) -> None:
        self._service = service

    async def upload_document(self, file: UploadFile, dto: UploadRequestDTO) -> DocumentResponseDTO:
        await validate_pdf(file)
        file_bytes = await file.read()
        filename = dto.custom_name or file.filename
        try:
            document = await self._service.process_pdf(file_bytes, filename)  # ← era process_document
        except DuplicateDocumentError as e:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
        return DocumentResponseDTO.from_entity(document)

    async def get_all_documents(self) -> list[DocumentResponseDTO]:
        documents = await self._service.get_all()
        return [DocumentResponseDTO.from_entity(d) for d in documents]

    async def get_document_by_id(self, document_id: str) -> DocumentResponseDTO:
        try:
            document = await self._service.get_by_id(document_id)
        except DocumentNotFoundError:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Documento '{document_id}' no encontrado.")
        return DocumentResponseDTO.from_entity(document)

    async def update_document(self, document_id: str, dto: UpdateRequestDTO) -> DocumentResponseDTO:
        try:
            document = await self._service.update(document_id, dto.model_dump(exclude_none=True))
        except DocumentNotFoundError:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Documento '{document_id}' no encontrado.")
        return DocumentResponseDTO.from_entity(document)

    async def delete_document(self, document_id: str) -> dict[str, str]:
        try:
            await self._service.delete(document_id)
        except DocumentNotFoundError:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Documento '{document_id}' no encontrado.")
        return {"message": f"Documento '{document_id}' eliminado correctamente."}