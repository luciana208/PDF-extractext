from fastapi import UploadFile, Response
from starlette.responses import StreamingResponse

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
            document = await self._service.process_pdf(file_bytes, filename)
        except DuplicateDocumentError:
            raise
        return DocumentResponseDTO.from_entity(document)

    async def get_all_documents(self, skip: int = 0, limit: int = 20) -> list[DocumentResponseDTO]:
        documents = await self._service.get_all(skip=skip, limit=limit)
        return [DocumentResponseDTO.from_entity(d) for d in documents]

    async def get_document_by_id(self, document_id: str) -> DocumentResponseDTO:
        try:
            document = await self._service.get_by_id(document_id)
        except DocumentNotFoundError as exc:
            raise exc
        return DocumentResponseDTO.from_entity(document)

    async def update_document(self, document_id: str, dto: UpdateRequestDTO) -> DocumentResponseDTO:
        try:
            document = await self._service.update(document_id, dto.model_dump(exclude_none=True))
        except DocumentNotFoundError as exc:
            raise exc
        return DocumentResponseDTO.from_entity(document)

    async def delete_document(self, document_id: str) -> dict[str, str]:
        try:
            await self._service.delete(document_id)
        except DocumentNotFoundError as exc:
            raise exc
        return {"message": f"Documento '{document_id}' eliminado correctamente."}

    async def download_document_text(self, document_id: str) -> Response:
        document = await self._service.get_by_id(document_id)
        # Use original filename but with .txt extension
        original = document.filename or document_id
        if original.lower().endswith(".pdf"):
            download_name = original[: -4] + ".txt"
        else:
            download_name = original + ".txt"

        # StreamingResponse expects an iterator of bytes
        async def stream_text():
            yield document.extracted_text.encode("utf-8")

        headers = {"Content-Disposition": f"attachment; filename=\"{download_name}\""}

        return StreamingResponse(stream_text(), media_type="text/plain; charset=utf-8", headers=headers)