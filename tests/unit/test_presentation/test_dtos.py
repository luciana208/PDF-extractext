"""
test_dtos.py — Tests unitarios para los DTOs de la capa de Presentación
=======================================================================
Verificamos que los DTOs:
  1. Acepten datos válidos sin errores.
  2. Rechacen datos inválidos con errores de validación de Pydantic.
  3. Sean inmutables (frozen=True).
  4. Tengan los campos correctos.

Los DTOs son el "contrato" del sistema. Si cambian sin querer, estos tests lo detectarán inmediatamente.
"""

import pytest
from datetime import datetime
from pydantic import ValidationError

from app.presentation.dto.request.upload_request import UploadRequestDTO
from app.presentation.dto.request.update_request import UpdateRequestDTO
from app.presentation.dto.response.document_response import DocumentResponseDTO


class TestUploadRequestDTO:

    def test_valid_dto_with_custom_name(self):
        """Debe crearse correctamente con un nombre personalizado."""
        dto = UploadRequestDTO(custom_name="Mi documento")
        assert dto.custom_name == "Mi documento"

    def test_valid_dto_without_custom_name(self):
        """El custom_name es opcional; sin él, debe ser None."""
        dto = UploadRequestDTO()
        assert dto.custom_name is None

    def test_dto_is_immutable(self):
        """Los DTOs deben ser inmutables (frozen=True)."""
        dto = UploadRequestDTO(custom_name="Original")
        with pytest.raises(Exception):  # ValidationError o AttributeError
            dto.custom_name = "Modificado"

    def test_custom_name_too_long_raises_validation_error(self):
        """Un nombre mayor a 255 caracteres debe fallar la validación."""
        with pytest.raises(ValidationError):
            UploadRequestDTO(custom_name="a" * 256)


class TestUpdateRequestDTO:

    def test_valid_dto_with_custom_name(self):
        """Debe crearse con un nuevo nombre."""
        dto = UpdateRequestDTO(custom_name="Nuevo nombre")
        assert dto.custom_name == "Nuevo nombre"

    def test_valid_dto_without_fields(self):
        """Todos los campos son opcionales; sin nada enviado, deben ser None."""
        dto = UpdateRequestDTO()
        assert dto.custom_name is None

    def test_dto_is_immutable(self):
        """Los DTOs de request también son inmutables."""
        dto = UpdateRequestDTO(custom_name="Original")
        with pytest.raises(Exception):
            dto.custom_name = "Modificado"


class TestDocumentResponseDTO:

    @pytest.fixture
    def valid_data(self) -> dict:
        """Datos mínimos válidos para construir un DocumentResponseDTO."""
        return {
            "id": "abc123",
            "name": "Documento de prueba",
            "checksum": "sha256fakehash",
            "extracted_text": "Texto del documento.",
            "created_at": datetime(2024, 1, 1),
            "updated_at": datetime(2024, 1, 1),
        }

    def test_valid_response_dto(self, valid_data):
        """Debe crearse correctamente con todos los campos requeridos."""
        dto = DocumentResponseDTO(**valid_data)
        assert dto.id == "abc123"
        assert dto.name == "Documento de prueba"
        assert dto.checksum == "sha256fakehash"

    def test_missing_required_field_raises_error(self, valid_data):
        """Si falta un campo requerido, Pydantic debe lanzar ValidationError."""
        del valid_data["checksum"]
        with pytest.raises(ValidationError):
            DocumentResponseDTO(**valid_data)

    def test_response_dto_is_immutable(self, valid_data):
        """El DTO de respuesta también es inmutable."""
        dto = DocumentResponseDTO(**valid_data)
        with pytest.raises(Exception):
            dto.name = "Modificado"

    def test_extracted_text_can_be_empty(self, valid_data):
        """El texto extraído puede ser vacío (PDF escaneado sin OCR)."""
        valid_data["extracted_text"] = ""
        dto = DocumentResponseDTO(**valid_data)
        assert dto.extracted_text == ""

    def test_text_preview_is_truncated_to_500_chars(self, valid_data):
        """El preview de texto debe limitarse a los primeros 500 caracteres."""
        valid_data["extracted_text"] = "a" * 550
        dto = DocumentResponseDTO(**valid_data)
        assert dto.text_preview == "a" * 500