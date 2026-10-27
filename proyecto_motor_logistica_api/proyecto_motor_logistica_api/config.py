"""Configuración del backend, leída de variables de entorno.

Los valores reales viven en el archivo .env (que NO se sube a Git).
El archivo .env.example muestra qué variables existen y sirve de plantilla.
"""

import os


def _como_booleano(nombre: str, por_defecto: bool = False) -> bool:
    valor = os.getenv(nombre)
    if valor is None:
        return por_defecto
    return valor.strip().lower() in ("1", "true", "t", "si", "sí", "yes", "y", "on")


def _es_marcador(valor: str) -> bool:
    """True si falta el valor o si sigue siendo el de ejemplo (todo ceros)."""
    return not valor or set(valor.replace("-", "")) <= {"0"}


# Modo local SIN Microsoft Entra ID: solo para desarrollo o revisión local.
AUTH_DISABLED = _como_booleano("AUTH_DISABLED")

AZURE_TENANT_ID = os.getenv("AZURE_TENANT_ID", "").strip()
AZURE_API_CLIENT_ID = os.getenv("AZURE_API_CLIENT_ID", "").strip()
AZURE_ALLOW_GUEST_USERS = _como_booleano("AZURE_ALLOW_GUEST_USERS")
SCOPE_API = f"api://{AZURE_API_CLIENT_ID}/access_as_user"

CORS_ORIGINS = [
    origen.strip()
    for origen in os.getenv("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(",")
    if origen.strip()
]
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")


def validar_autenticacion() -> None:
    """Falla al arrancar, con un mensaje claro, si falta configurar Entra ID."""
    if AUTH_DISABLED:
        return
    faltan = [
        nombre
        for nombre, valor in (("AZURE_TENANT_ID", AZURE_TENANT_ID), ("AZURE_API_CLIENT_ID", AZURE_API_CLIENT_ID))
        if _es_marcador(valor)
    ]
    if faltan:
        raise RuntimeError(
            "Falta configurar Microsoft Entra ID: define " + " y ".join(faltan) + " en el archivo .env "
            "(ver README, sección 'Registrar las apps en Microsoft Entra ID'). "
            "Para probar en local sin Entra ID usa AUTH_DISABLED=true."
        )
