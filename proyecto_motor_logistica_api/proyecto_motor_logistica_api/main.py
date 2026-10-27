"""Punto de entrada de la API del Motor de Optimización Logística.

Aquí solo se arma la aplicación; la lógica vive en módulos:
  - config.py / seguridad.py / database.py  configuración, autenticación y conexión
  - schemas.py                              modelos de entrada y salida
  - servicios/                              ruta óptima (TSP) y predicción de demanda
  - routers/                                endpoints agrupados por sección
  - agente_espacio.py / agente_mensajes.py  agentes de recomendación y mensajes
"""

import logging
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_swagger_ui_oauth2_redirect_html
from fastapi.responses import HTMLResponse

import config
import models  # noqa: F401  (registra las tablas en SQLAlchemy)
from database import Base, engine
from docs_tema import construir_docs_html
from routers import almacen, analisis, asistente, paquetes
from routers.etiquetas import ETIQUETAS
from seguridad import esquema_azure

logger = logging.getLogger("uvicorn.error")


@asynccontextmanager
async def lifespan(app: FastAPI):
    if esquema_azure is not None:
        # Descarga las claves públicas de Entra ID con las que se validan los tokens
        await esquema_azure.openid_config.load_config()
    else:
        logger.warning("AUTH_DISABLED=true: la API NO valida tokens. Úsalo solo en local.")
    yield


DESCRIPCION = (
    "Rutas de picking, paquetes por rack, análisis de inventario y asistente por rol. "
    + (
        "Modo local: la autenticación está desactivada (AUTH_DISABLED=true)."
        if config.AUTH_DISABLED
        else "Todos los endpoints requieren iniciar sesión con Microsoft Entra ID."
    )
)

app = FastAPI(
    title="Motor de Optimización Logística",
    version="1.4.0",
    description=DESCRIPCION,
    openapi_tags=ETIQUETAS,
    docs_url=None,  # /docs se sirve más abajo, con el tema propio (docs_tema.py)
    swagger_ui_oauth2_redirect_url="/oauth2-redirect",
    swagger_ui_init_oauth=None
    if config.AUTH_DISABLED
    else {
        "usePkceWithAuthorizationCodeGrant": True,
        "clientId": config.AZURE_API_CLIENT_ID,
        "scopes": config.SCOPE_API,
    },
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Base.metadata.create_all(bind=engine)

for router in (almacen.router, paquetes.router, analisis.router, asistente.router):
    app.include_router(router)


@app.get("/docs", include_in_schema=False)
async def documentacion():
    return HTMLResponse(construir_docs_html(app))


@app.get("/oauth2-redirect", include_in_schema=False)
async def oauth2_redirect():
    # Página a la que Microsoft regresa tras iniciar sesión desde el botón Authorize
    return get_swagger_ui_oauth2_redirect_html()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
