"""Autenticación de la API.

- Normal: se validan los tokens de Microsoft Entra ID (fastapi-azure-auth).
- AUTH_DISABLED=true: no se valida nada (solo desarrollo o revisión local).

Los routers usan `Security(requerir_autenticacion)` sin importar el modo.
"""

import config

config.validar_autenticacion()

if config.AUTH_DISABLED:
    esquema_azure = None

    async def requerir_autenticacion() -> dict:
        return {"usuario": "modo-local"}

else:
    from fastapi_azure_auth import SingleTenantAzureAuthorizationCodeBearer

    esquema_azure = SingleTenantAzureAuthorizationCodeBearer(
        app_client_id=config.AZURE_API_CLIENT_ID,
        tenant_id=config.AZURE_TENANT_ID,
        scopes={config.SCOPE_API: "access_as_user"},
        allow_guest_users=config.AZURE_ALLOW_GUEST_USERS,
    )
    requerir_autenticacion = esquema_azure
