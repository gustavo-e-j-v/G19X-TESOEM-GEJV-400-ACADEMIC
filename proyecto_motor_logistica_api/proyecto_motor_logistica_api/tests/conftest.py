"""Configuración común de las pruebas.

Las pruebas usan SQLite en memoria y la autenticación desactivada: nunca tocan
PostgreSQL ni Entra ID. Estas variables se fijan ANTES de importar la aplicación.
"""

import os

os.environ["DATABASE_URL"] = "sqlite://"
os.environ["AUTH_DISABLED"] = "true"

import pytest
from fastapi.testclient import TestClient

import models  # noqa: F401
from database import Base, SessionLocal, engine


@pytest.fixture()
def db():
    """Sesión sobre una base vacía para cada prueba."""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    sesion = SessionLocal()
    try:
        yield sesion
    finally:
        sesion.close()


@pytest.fixture()
def client(db):
    from main import app

    return TestClient(app)
