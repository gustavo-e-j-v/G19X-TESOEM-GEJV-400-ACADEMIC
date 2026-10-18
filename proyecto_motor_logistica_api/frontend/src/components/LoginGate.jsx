import { useMsal } from "@azure/msal-react";
import { loginRequest } from "../authConfig";

export default function LoginGate() {
  const { instance } = useMsal();

  function handleLogin() {
    instance.loginRedirect(loginRequest);
  }

  return (
    <div className="login-gate">
      <div className="login-card">
        <h1 className="panel-title">Ruta de picking</h1>
        <p className="panel-subtitle">Inicia sesión con tu cuenta de la organización para continuar.</p>
        <button className="submit-btn" onClick={handleLogin}>
          Iniciar sesión con Microsoft
        </button>
      </div>
    </div>
  );
}
