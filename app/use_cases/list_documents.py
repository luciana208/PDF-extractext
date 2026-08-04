class ListDocumentsUseCase:
    def __init__(self, repository) -> None:
        self._repository = repository

    async def execute(self, skip: int = 0, limit: int = 20):
        return await self._repository.get_all(skip=skip, limit=limit)
