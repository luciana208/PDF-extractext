from fastapi import UploadFile, Response
from starlette.responses import StreamingResponse

from app.business.domain.exceptions import DocumentNotFoundError, DuplicateDocumentError
from app.use_cases.process_pdf import ProcessPDFUseCase
from app.use_cases.list_documents import ListDocumentsUseCase
from app.use_cases.get_document import GetDocumentUseCase
from app.use_cases.update_document import UpdateDocumentUseCase
from app.use_cases.delete_document import DeleteDocumentUseCase
from app.use_cases.download_text import DownloadTextUseCase
from app.presentation.dto.request.update_request import UpdateRequestDTO
from app.presentation.dto.request.upload_request import UploadRequestDTO
from app.presentation.dto.response.document_response import DocumentResponseDTO
from app.presentation.validators.pdf_validator import validate_pdf


class DocumentController:

    def __init__(
        self,
        process_pdf: ProcessPDFUseCase,
        list_documents: ListDocumentsUseCase,
        get_document: GetDocumentUseCase,
        update_document: UpdateDocumentUseCase,
        delete_document: DeleteDocumentUseCase,
        download_text: DownloadTextUseCase,
    ) -> None:
        self._process_pdf = process_pdf
        self._list_documents = list_documents
        self._get_document = get_document
        self._update_document = update_document
        self._delete_document = delete_document
        self._download_text = download_text

    async def upload_document(self, file: UploadFile, dto: UploadRequestDTO) -> DocumentResponseDTO:
        await validate_pdf(file)
        file_bytes = await file.read()
        filename = dto.custom_name or file.filename
        try:
            document = await self._process_pdf.execute(file_bytes, filename)
        except DuplicateDocumentError:
            raise
        return DocumentResponseDTO.from_entity(document)

    async def get_all_documents(self, skip: int = 0, limit: int = 20) -> list[DocumentResponseDTO]:
        documents = await self._list_documents.execute(skip=skip, limit=limit)
        return [DocumentResponseDTO.from_entity(d) for d in documents]

    async def get_document_by_id(self, document_id: str) -> DocumentResponseDTO:
        try:
            document = await self._get_document.execute(document_id)
        except DocumentNotFoundError as exc:
            raise exc
        return DocumentResponseDTO.from_entity(document)

    async def update_document(self, document_id: str, dto: UpdateRequestDTO) -> DocumentResponseDTO:
        try:
            document = await self._update_document.execute(document_id, dto.model_dump(exclude_none=True))
        except DocumentNotFoundError as exc:
            raise exc
        return DocumentResponseDTO.from_entity(document)

    async def delete_document(self, document_id: str) -> dict[str, str]:
        try:
            await self._delete_document.execute(document_id)
        except DocumentNotFoundError as exc:
            raise exc
        return {"message": f"Documento '{document_id}' eliminado correctamente."}

    async def download_document_text(self, document_id: str) -> Response:
        # Use the download use case to fetch the document for download
        document = await self._download_text.execute(document_id)
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