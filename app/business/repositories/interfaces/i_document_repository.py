from ABC import ABC, abstractmethod
from typing import Optional
from app.business.entities.document import Document 

class IDocumentRepository(ABC):
    @abstractmethod
    async def save(self, document: Document) -> Document: