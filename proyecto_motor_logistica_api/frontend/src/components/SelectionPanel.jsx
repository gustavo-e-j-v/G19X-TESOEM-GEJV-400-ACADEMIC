export default function SelectionPanel({
  ubicaciones,
  origenId,
  setOrigenId,
  seleccionados,
  onSubmit,
  cargando,
}) {
  return (
    <aside className="panel">
      <div>
        <h1 className="panel-title">Ruta de picking</h1>
        <p className="panel-subtitle">
          Elige el punto de salida, luego haz clic en los estantes que quieres visitar.
        </p>
      </div>

      <label className="field">
        <span className="field-label">Punto de salida</span>
        <select value={origenId} onChange={(e) => setOrigenId(e.target.value)} className="select">
          {ubicaciones.map((u) => (
            <option key={u.id} value={u.id}>
              {u.id}
            </option>
          ))}
        </select>
      </label>

      <div className="selected-count">
        <span className="stat-value">{seleccionados.length}</span>
        <span className="stat-label">estantes seleccionados</span>
      </div>

      <button
        className="submit-btn"
        onClick={onSubmit}
        disabled={cargando || seleccionados.length === 0}
      >
        {cargando ? "Calculando…" : "Calcular ruta óptima"}
      </button>
    </aside>
  );
}
