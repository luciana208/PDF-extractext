"""
Fixtures globales de pytest para la capa de Negocio.

Este archivo es detectado automáticamente por pytest. Las fixtures
definidas aquí están disponibles en todos los tests sin necesidad
de importarlas explícitamente.
"""

import pytest
import pytest_asyncio


@pytest.fixture(scope="session")
def sample_pdf_bytes() -> bytes:
    """Bytes mínimos que simulan un PDF válido para tests unitarios.

    Para tests de integración que necesitan un PDF real, usar
    tests/fixtures/sample.pdf directamente.
    """
    return b"%PDF-1.4 1 0 obj<</Type/Catalog>>endobj"


@pytest.fixture(scope="session")
def known_checksum() -> str:
    """Checksum SHA-256 del sample_pdf_bytes para assertions en tests."""
    import hashlib

    data = b"%PDF-1.4 1 0 obj<</Type/Catalog>>endobj"
    return hashlib.sha256(data).hexdigest()