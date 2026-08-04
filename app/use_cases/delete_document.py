from app.business.domain.exceptions import DocumentNotFoundError


class DeleteDocumentUseCase:
    def __init__(self, repository) -> None:
        self._repository = repository

    async def execute(self, document_id: str) -> None:
        deleted = await self._repository.delete(document_id)
        if not deleted:
            raise DocumentNotFoundError(document_id)
