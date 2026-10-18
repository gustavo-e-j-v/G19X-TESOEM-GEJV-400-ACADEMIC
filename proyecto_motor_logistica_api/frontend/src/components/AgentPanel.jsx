import { formatearFecha, textoPlazo } from "../formato";

const ETIQUETAS = { urgente: "Urgente", aviso: "Aviso", consejo: "Consejo", info: "Info" };
const ROLES = [
  { id: "empleado", nombre: "Empleado" },
  { id: "encargado", nombre: "Encargado" },
];

// Panel del asistente: mensajes de apoyo según el rol y la entrega más próxima.
export default function AgentPanel({ rol, setRol, datos, cargando, error }) {
  const proximo = datos?.paquete_mas_proximo;

  return (
    <section className="agent-panel">
      <div className="agent-head">
        <h2 className="agent-title">Asistente</h2>
        <div className="role-toggle" role="group" aria-label="Rol">
          {ROLES.map((r) => (
            <button
              key={r.id}
              type="button"
              className={`role-btn ${rol === r.id ? "role-active" : ""}`}
              onClick={() => setRol(r.id)}
            >
              {r.nombre}
            </button>
          ))}
        </div>
      </div>

      {error && <p className="agent-error">{error}</p>}
      {cargando && !datos && <p className="agent-dim">Analizando…</p>}

      {proximo && (
        <div className="next-delivery">
          <span className="next-label">Entrega más próxima</span>
          <span className="next-main">
            {proximo.codigo} · {proximo.rack_id}
          </span>
          <span className="next-date">
            {formatearFecha(proximo.fecha_entrega)} · {textoPlazo(proximo.dias_restantes)}
          </span>
        </div>
      )}

      {datos && <p className="agent-summary">{datos.resumen}</p>}

      <ul className="agent-messages">
        {datos?.mensajes.map((m, i) => (
          <li key={i} className={`agent-msg msg-${m.tipo}`}>
            <span className="msg-tag">{ETIQUETAS[m.tipo] ?? m.tipo}</span>
            {m.texto}
          </li>
        ))}
      </ul>
    </section>
  );
}
