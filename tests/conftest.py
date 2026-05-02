"""
conftest.py — Fixtures globales de pytest
==========================================
Este archivo es detectado automáticamente por pytest. Las fixtures
definidas aquí están disponibles en todos los tests sin necesidad
de importarlas explícitamente.

IMPORTANTE — Base de datos de test aislada:
  Los tests de integración conectan a MongoDB real. Para que no borren
  los datos de desarrollo, forzamos una DB separada (pdf_test_db) antes
  de que cualquier módulo de la app se importe.

  El orden es crítico: os.environ debe modificarse ANTES de que
  app.config.settings se evalúe por primera vez, porque Settings lee
  las variables de entorno en tiempo de importación.

  Si querés usar otra DB de test, podés sobreescribir con:
      DB_NAME=mi_db_test pytest tests/
"""

import os

# ------------------------------------------------------------------ #
# Forzar DB de test ANTES de cualquier importación de la app
# ------------------------------------------------------------------ #

# Solo sobreescribimos DB_NAME si no fue definida explícitamente desde
# la terminal (por ejemplo: DB_NAME=otra_db pytest tests/).
# Así el desarrollador sigue teniendo control total si lo necesita.
os.environ.setdefault("DB_NAME", "pdf_test_db")

# ------------------------------------------------------------------ #
# Imports normales (después de fijar el entorno)
# ------------------------------------------------------------------ #

import pytest


# ------------------------------------------------------------------ #
# Fixtures globales
# ------------------------------------------------------------------ #

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