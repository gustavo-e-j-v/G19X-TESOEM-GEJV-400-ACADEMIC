import { useEffect, useState } from "react";

// Ventana para confirmar que la ruta se surtió: se capturan las unidades recogidas en cada rack.
export default function SurtidoModal({ racks, onCerrar, onConfirmar }) {
  const [unidades, setUnidades] = useState(() => Object.fromEntries(racks.map((id) => [id, "1"])));
  const [guardando, setGuardando] = useState(false);
  const [error, setError] = useState(null);

  // Cerrar con la tecla Esc
  useEffect(() => {
    function alPresionar(e) {
      if (e.key === "Escape") onCerrar();
    }
    window.addEventListener("keydown", alPresionar);
    return () => window.removeEventListener("keydown", alPresionar);
  }, [onCerrar]);

  const valido = racks.every((id) => Number.isInteger(Number(unidades[id])) && Number(unidades[id]) >= 1);

  async function confirmar(e) {
    e.preventDefault();
    setGuardando(true);
    setError(null);
    try {
      await onConfirmar(racks.map((id) => ({ rack_id: id, unidades: Number(unidades[id]) })));
    } catch (err) {
      setError(err.message);
      setGuardando(false);
    }
  }

  return (
    <div className="modal-overlay" onClick={onCerrar}>
      <form
        className="modal"
        role="dialog"
        aria-modal="true"
        aria-label="Confirmar ruta surtida"
        onClick={(e) => e.stopPropagation()}
        onSubmit={confirmar}
      >
        <div className="modal-head">
          <div>
            <h2 className="modal-title">Ruta surtida</h2>
            <p className="modal-sub">
              Indica cuántas unidades se recogieron en cada rack. Se guardan en el historial de picking y
              alimentan la clasificación ABC y la predicción de demanda.
            </p>
          </div>
          <button type="button" className="modal-close" onClick={onCerrar} aria-label="Cerrar">
            ×
          </button>
        </div>

        {error && <div className="error-banner">{error}</div>}

        <ul className="pkg-list">
          {racks.map((id) => (
            <li key={id} className="pkg-item">
              <span className="pkg-code surtido-rack">{id}</span>
              <label className="surtido-campo">
                <span className="field-label">Unidades</span>
                <input
                  className="input"
                  type="number"
                  min="1"
                  max="100000"
                  step="1"
                  value={unidades[id]}
                  onChange={(e) => setUnidades({ ...unidades, [id]: e.target.value })}
                  required
                />
              </label>
            </li>
          ))}
        </ul>

        <button type="submit" className="submit-btn" disabled={guardando || !valido}>
          {guardando ? "Guardando…" : "Confirmar ruta surtida"}
        </button>
      </form>
    </div>
  );
}
