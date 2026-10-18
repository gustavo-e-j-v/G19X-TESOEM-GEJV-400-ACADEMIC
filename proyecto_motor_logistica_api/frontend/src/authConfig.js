// Identificadores de Microsoft Entra ID (Portal de Azure > Registros de aplicaciones).
const TENANT_ID = "fea7c33e-0fa3-43f3-aeb6-d5d6a25c855c";
const FRONTEND_CLIENT_ID = "252efc1d-84d8-4475-a175-195c16016f16";
const API_CLIENT_ID = "1fc0a49f-ce9e-43c1-a35b-dea22b55d8c5";

export const msalConfig = {
  auth: {
    clientId: FRONTEND_CLIENT_ID,
    authority: `https://login.microsoftonline.com/${TENANT_ID}`,
    redirectUri: "http://localhost:5173",
  },
  cache: {
    cacheLocation: "sessionStorage",
    storeAuthStateInCookie: false,
  },
};

// El "scope" que le pedimos a Entra ID: permiso para llamar a nuestra propia API.
export const loginRequest = {
  scopes: [`api://${API_CLIENT_ID}/access_as_user`],
};
