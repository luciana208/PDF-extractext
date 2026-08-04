from app.business.domain.exceptions import DocumentNotFoundError


class UpdateDocumentUseCase:
    def __init__(self, repository) -> None:
        self._repository = repository

    async def execute(self, document_id: str, fields: dict):
        updated = await self._repository.update(document_id, fields)
        if updated is None:
            raise DocumentNotFoundError(document_id)
        return updated
