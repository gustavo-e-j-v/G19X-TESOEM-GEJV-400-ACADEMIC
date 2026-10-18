import { useCallback, useEffect, useState } from "react";
import { fetchPaquetes, crearPaquete, eliminarPaquete } from "../api";
import { formatearFecha, textoPlazo, claseUrgencia, textoPaquetes } from "../formato";

const FORM_VACIO = { codigo: "", descripcion: "", fecha_entrega: "" };

// Ventana emergente de un rack: lista sus paquetes y permite registrar nuevos.
export default function RackModal({ rack, obtenerToken, onCerrar, onCambio }) {
  const [paquetes, setPaquetes] = useState([]);
  const [cargando, setCargando] = useState(true);
  const [guardando, setGuardando] = useState(false);
  const [error, setError] = useState(null);
  const [form, setForm] = useState(FORM_VACIO);

  const cargar = useCallback(async () => {
    try {
      const token = await obtenerToken();
      setPaquetes(await fetchPaquetes(rack.id, token));
      setError(null);
    } catch (e) {
      setError(e.message);
    } finally {
      setCargando(false);
    }
  }, [rack.id, obtenerToken]);

  useEffect(() => {
    cargar();
  }, [cargar]);

  // Cerrar con la tecla Esc
  useEffect(() => {
    function alPresionar(e) {
      if (e.key === "Escape") onCerrar();
    }
    window.addEventListener("keydown", alPresionar);
    return () => window.removeEventListener("keydown", alPresionar);
  }, [onCerrar]);

  const campo = (nombre) => (e) => setForm({ ...form, [nombre]: e.target.value });

  async function handleAgregar(e) {
    e.preventDefault();
    setGuardando(true);
    setError(null);
    try {
      const token = await obtenerToken();
      await crearPaquete(rack.id, form, token);
      setForm(FORM_VACIO);
      await cargar();
      onCambio();
    } catch (err) {
      setError(err.message);
    } finally {
      setGuardando(false);
    }
  }

  async function handleEliminar(paquete) {
    if (!window.confirm(`¿Eliminar el paquete ${paquete.codigo}?`)) return;
    try {
      const token = await obtenerToken();
      await eliminarPaquete(paquete.id, token);
      await cargar();
      onCambio();
    } catch (err) {
      setError(err.message);
    }
  }

  const proxima = paquetes[0];

  return (
    <div className="modal-overlay" onClick={onCerrar}>
      <div
        className="modal"
        role="dialog"
        aria-modal="true"
        aria-label={`Paquetes de ${rack.id}`}
        onClick={(e) => e.stopPropagation()}
      >
        <div className="modal-head">
          <div>
            <h2 className="modal-title">{rack.id}</h2>
            <p className="modal-sub">
              Pasillo {rack.y} · {textoPaquetes(paquetes.length)}
              {proxima ? ` · próxima entrega ${formatearFecha(proxima.fecha_entrega)}` : ""}
            </p>
          </div>
          <button type="button" className="modal-close" onClick={onCerrar} aria-label="Cerrar">
            ×
          </button>
        </div>

        {error && <div className="error-banner">{error}</div>}

        <ul className="pkg-list">
          {cargando && <li className="pkg-empty">Cargando…</li>}
          {!cargando && paquetes.length === 0 && (
            <li className="pkg-empty">Este rack no tiene paquetes registrados.</li>
          )}
          {paquetes.map((p) => (
            <li key={p.id} className="pkg-item">
              <div className="pkg-main">
                <span className="pkg-code">{p.codigo}</span>
                {p.descripcion && <span className="pkg-desc">{p.descripcion}</span>}
              </div>
              <div className="pkg-side">
                <span className="pkg-date">{formatearFecha(p.fecha_entrega)}</span>
                <span className={`pkg-chip ${claseUrgencia(p.dias_restantes)}`}>
                  {textoPlazo(p.dias_restantes)}
                </span>
              </div>
              <button
                type="button"
                className="pkg-delete"
                onClick={() => handleEliminar(p)}
                aria-label={`Eliminar ${p.codigo}`}
              >
                Eliminar
              </button>
            </li>
          ))}
        </ul>

        <form className="pkg-form" onSubmit={handleAgregar}>
          <h3 className="pkg-form-title">Agregar paquete</h3>
          <label className="field">
            <span className="field-label">Código o guía</span>
            <input className="input" value={form.codigo} onChange={campo("codigo")} required maxLength={60} />
          </label>
          <label className="field">
            <span className="field-label">Descripción (opcional)</span>
            <input className="input" value={form.descripcion} onChange={campo("descripcion")} maxLength={200} />
          </label>
          <label className="field">
            <span className="field-label">Fecha de entrega</span>
            <input
              className="input"
              type="date"
              value={form.fecha_entrega}
              onChange={campo("fecha_entrega")}
              required
            />
          </label>
          <button type="submit" className="submit-btn" disabled={guardando}>
            {guardando ? "Guardando…" : "Agregar paquete"}
          </button>
        </form>
      </div>
    </div>
  );
}
