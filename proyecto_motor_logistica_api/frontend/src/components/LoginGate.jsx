import { useAuth } from "../auth";

export default function LoginGate() {
  const { iniciarSesion } = useAuth();

  return (
    <div className="login-gate">
      <div className="login-card">
        <h1 className="panel-title">Ruta de picking</h1>
        <p className="panel-subtitle">Inicia sesión con tu cuenta de la organización para continuar.</p>
        <button className="submit-btn" onClick={iniciarSesion}>
          Iniciar sesión con Microsoft
        </button>
      </div>
    </div>
  );
}
