// Configuración de Microsoft Entra ID. Los identificadores se leen de variables
// VITE_* (archivo .env del frontend, ver .env.example); no están escritos en el código.
const env = import.meta.env;

export const AUTH_DISABLED = env.VITE_AUTH_DISABLED === "true";

const TENANT_ID = env.VITE_AZURE_TENANT_ID;
const FRONTEND_CLIENT_ID = env.VITE_AZURE_FRONTEND_CLIENT_ID;
const API_CLIENT_ID = env.VITE_AZURE_API_CLIENT_ID;
const REDIRECT_URI = env.VITE_REDIRECT_URI || window.location.origin;

// Vacío o todavía con el valor de ejemplo (todo ceros)
const faltante = (valor) => !valor || /^[0-]+$/.test(valor);

export const variablesFaltantes = AUTH_DISABLED
  ? []
  : [
      ["VITE_AZURE_TENANT_ID", TENANT_ID],
      ["VITE_AZURE_FRONTEND_CLIENT_ID", FRONTEND_CLIENT_ID],
      ["VITE_AZURE_API_CLIENT_ID", API_CLIENT_ID],
    ]
      .filter(([, valor]) => faltante(valor))
      .map(([nombre]) => nombre);

export const msalConfig = {
  auth: {
    clientId: FRONTEND_CLIENT_ID,
    authority: `https://login.microsoftonline.com/${TENANT_ID}`,
    redirectUri: REDIRECT_URI,
  },
  cache: {
    cacheLocation: "sessionStorage",
    storeAuthStateInCookie: false,
  },
};

// Permiso que se le pide a Entra ID: llamar a la API del backend
export const loginRequest = {
  scopes: [`api://${API_CLIENT_ID}/access_as_user`],
};
