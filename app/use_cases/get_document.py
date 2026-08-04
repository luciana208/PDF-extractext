from app.business.domain.exceptions import DocumentNotFoundError


class GetDocumentUseCase:
    def __init__(self, repository) -> None:
        self._repository = repository

    async def execute(self, document_id: str):
        document = await self._repository.get_by_id(document_id)
        if document is None:
            raise DocumentNotFoundError(document_id)
        return document
