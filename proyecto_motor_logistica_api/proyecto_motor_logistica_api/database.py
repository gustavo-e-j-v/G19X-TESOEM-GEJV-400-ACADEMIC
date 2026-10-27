"""Conexión a la base de datos.

La contraseña NUNCA va en el código: se lee de variables de entorno
(archivo .env, ver .env.example). Se puede indicar la URL completa con
DATABASE_URL o los datos sueltos con POSTGRES_*.
"""

import os
from urllib.parse import quote_plus

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from sqlalchemy.pool import StaticPool


def _construir_url() -> str:
    url = os.getenv("DATABASE_URL")
    if url:
        return url

    clave = os.getenv("POSTGRES_PASSWORD")
    if not clave:
        raise RuntimeError(
            "Falta la contraseña de la base de datos. Copia .env.example como .env y define "
            "POSTGRES_PASSWORD (o define DATABASE_URL)."
        )
    usuario = os.getenv("POSTGRES_USER", "postgres")
    host = os.getenv("POSTGRES_HOST", "localhost")
    puerto = os.getenv("POSTGRES_PORT", "5432")
    nombre = os.getenv("POSTGRES_DB", "almacen_db")
    return f"postgresql://{quote_plus(usuario)}:{quote_plus(clave)}@{host}:{puerto}/{nombre}"


DATABASE_URL = _construir_url()

if DATABASE_URL.startswith("sqlite"):
    # SQLite (solo pruebas): una única conexión compartida entre hilos
    engine = create_engine(
        DATABASE_URL, echo=False, connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
else:
    engine = create_engine(DATABASE_URL, echo=False)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
