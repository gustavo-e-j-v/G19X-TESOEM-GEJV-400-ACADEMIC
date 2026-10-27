// Punto único de acceso a la sesión. La aplicación usa useAuth() sin saber si
// hay Microsoft Entra ID o si se está en modo local (VITE_AUTH_DISABLED=true).
import { useCallback } from "react";
import { useIsAuthenticated, useMsal } from "@azure/msal-react";
import { AUTH_DISABLED, loginRequest } from "./authConfig";

function useAuthMsal() {
  const autenticado = useIsAuthenticated();
  const { instance, accounts } = useMsal();

  // Pide un token de acceso en silencio (sin volver a mostrar el login si ya hay sesión)
  const obtenerToken = useCallback(async () => {
    const respuesta = await instance.acquireTokenSilent({ ...loginRequest, account: accounts[0] });
    return respuesta.accessToken;
  }, [instance, accounts]);

  return {
    autenticado,
    usuario: accounts[0]?.username ?? "",
    local: false,
    obtenerToken,
    iniciarSesion: () => instance.loginRedirect(loginRequest),
    cerrarSesion: () => instance.logoutRedirect(),
  };
}

// Sesión fija para el modo local: no hay token ni pantalla de login
const SESION_LOCAL = {
  autenticado: true,
  usuario: "modo local",
  local: true,
  obtenerToken: async () => null,
  iniciarSesion: () => {},
  cerrarSesion: () => {},
};

function useAuthLocal() {
  return SESION_LOCAL;
}

// AUTH_DISABLED es una constante de compilación, por lo que siempre se usa el mismo hook
export const useAuth = AUTH_DISABLED ? useAuthLocal : useAuthMsal;
