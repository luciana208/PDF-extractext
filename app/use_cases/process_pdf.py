from app.business.domain.checksum_calculator import calculate_checksum
from app.business.domain.text_extractor import extract_text
from app.business.domain.validators.document_validator import validate_no_duplicate
from app.business.entities.document import Document


class ProcessPDFUseCase:
    def __init__(self, repository) -> None:
        self._repository = repository

    async def execute(self, file_bytes: bytes, filename: str) -> Document:
        checksum = calculate_checksum(file_bytes)
        existing = await self._repository.get_by_checksum(checksum)
        validate_no_duplicate(existing, checksum)

        extracted_text = extract_text(file_bytes)

        document = Document(
            filename=filename,
            checksum=checksum,
            extracted_text=extracted_text,
        )

        return await self._repository.save(document)
