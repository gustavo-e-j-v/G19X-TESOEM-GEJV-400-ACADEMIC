import "../App.css";

// Se muestra cuando falta configurar el archivo .env del frontend
export default function ConfigError({ faltantes }) {
  return (
    <div className="login-gate">
      <div className="login-card" style={{ maxWidth: 520, textAlign: "left" }}>
        <h1 className="panel-title">Falta configurar el frontend</h1>
        <p className="panel-subtitle">
          Copia <code>.env.example</code> como <code>.env</code> (en la carpeta <code>frontend</code>), completa
          estos valores y reinicia <code>npm run dev</code>:
        </p>
        <ul>
          {faltantes.map((nombre) => (
            <li key={nombre}>
              <code>{nombre}</code>
            </li>
          ))}
        </ul>
        <p className="panel-subtitle">
          Para probar sin Microsoft Entra ID, usa <code>VITE_AUTH_DISABLED=true</code> (y{" "}
          <code>AUTH_DISABLED=true</code> en el backend). La guía completa está en el README.
        </p>
      </div>
    </div>
  );
}
