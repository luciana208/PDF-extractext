"""
Tests unitarios para checksum_calculator.

Valida que el cálculo de SHA-256 sea correcto, idempotente y sensible
a diferencias en el contenido. Sin mocks: es una función pura.
"""

import hashlib

import pytest

from app.business.domain.checksum_calculator import calculate_checksum


class TestCalculateChecksum:
    def test_returns_correct_sha256_for_known_input(self):
        """El hash generado debe coincidir con el SHA-256 estándar."""
        data = b"hello world"
        expected = hashlib.sha256(data).hexdigest()

        assert calculate_checksum(data) == expected

    def test_returns_64_char_hex_string(self):
        """SHA-256 siempre produce un hexdigest de 64 caracteres."""
        result = calculate_checksum(b"any content")

        assert isinstance(result, str)
        assert len(result) == 64

    def test_is_idempotent(self):
        """El mismo input siempre produce el mismo output."""
        data = b"consistent content"

        assert calculate_checksum(data) == calculate_checksum(data)

    def test_different_content_produces_different_checksum(self):
        """Archivos distintos deben tener checksums distintos."""
        assert calculate_checksum(b"file_a") != calculate_checksum(b"file_b")

    def test_empty_bytes_returns_known_hash(self):
        """El hash de bytes vacíos es el SHA-256 del string vacío (definido por el estándar)."""
        expected = hashlib.sha256(b"").hexdigest()

        assert calculate_checksum(b"") == expected

    def test_handles_large_input(self):
        """No debe fallar con archivos grandes (simulados con bytes repetidos)."""
        large_data = b"x" * 10_000_000  # 10 MB

        result = calculate_checksum(large_data)

        assert len(result) == 64