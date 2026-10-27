import { useEffect, useState } from "react";
import { fetchAnalisisAbc, fetchPrediccion, fetchRecomendaciones } from "../api";
import Sparkline from "./Sparkline";

const CLASES = [
  { id: "A", nombre: "Alta rotación" },
  { id: "B", nombre: "Rotación media" },
  { id: "C", nombre: "Baja rotación" },
];
const TENDENCIAS = {
  creciente: { icono: "↗", texto: "Creciente" },
  estable: { icono: "→", texto: "Estable" },
  decreciente: { icono: "↘", texto: "Decreciente" },
};

const numero = (n, decimales = 0) =>
  Number(n).toLocaleString("es-MX", { minimumFractionDigits: decimales, maximumFractionDigits: decimales });

// Vista de análisis: clasificación ABC, predicción de demanda por rack y recomendaciones de reubicación
export default function AnalisisView({ obtenerToken }) {
  const [abc, setAbc] = useState({ datos: null, error: null, cargando: true });
  const [reco, setReco] = useState({ datos: null, error: null, cargando: true });
  const [rack, setRack] = useState("");
  const [pred, setPred] = useState({ datos: null, error: null, cargando: false });

  // ABC y recomendaciones se piden juntas al entrar a la vista
  useEffect(() => {
    let activo = true;
    (async () => {
      try {
        const token = await obtenerToken();
        const [a, r] = await Promise.allSettled([fetchAnalisisAbc(token), fetchRecomendaciones(token)]);
        if (!activo) return;
        if (a.status === "fulfilled") {
          setAbc({ datos: a.value, error: null, cargando: false });
          setRack((actual) => actual || a.value[0]?.rack_id || "");
        } else {
          setAbc({ datos: null, error: a.reason.message, cargando: false });
        }
        setReco(
          r.status === "fulfilled"
            ? { datos: r.value, error: null, cargando: false }
            : { datos: null, error: r.reason.message, cargando: false }
        );
      } catch (e) {
        if (!activo) return;
        setAbc({ datos: null, error: e.message, cargando: false });
        setReco({ datos: null, error: e.message, cargando: false });
      }
    })();
    return () => {
      activo = false;
    };
  }, [obtenerToken]);

  // La predicción se pide cada vez que se elige otro rack
  useEffect(() => {
    if (!rack) return;
    let activo = true;
    setPred((p) => ({ ...p, cargando: true, error: null }));
    (async () => {
      try {
        const token = await obtenerToken();
        const datos = await fetchPrediccion(rack, token);
        if (activo) setPred({ datos, error: null, cargando: false });
      } catch (e) {
        if (activo) setPred({ datos: null, error: e.message, cargando: false });
      }
    })();
    return () => {
      activo = false;
    };
  }, [rack, obtenerToken]);

  const filas = abc.datos ?? [];
  const maximo = Math.max(1, ...filas.map((f) => f.porcentaje_del_total));

  return (
    <div className="analisis">
      {/* ---------- Clasificación ABC ---------- */}
      <section className="card">
        <header>
          <h2 className="card-title">Clasificación ABC</h2>
          <p className="card-sub">
            Racks ordenados por unidades recogidas. A concentra hasta el 80% del movimiento, B hasta el 95% y C el resto.
          </p>
        </header>

        {abc.cargando && <p className="muted">Cargando…</p>}
        {abc.error && <p className="aviso-error">{abc.error}</p>}

        {abc.datos && (
          <>
            <div className="clases">
              {CLASES.map((c) => {
                const delGrupo = filas.filter((f) => f.clase === c.id);
                const porcentaje = delGrupo.reduce((suma, f) => suma + f.porcentaje_del_total, 0);
                return (
                  <div key={c.id} className="clase-tile" data-clase={c.id}>
                    <span className="clase-chip" data-clase={c.id}>{c.id}</span>
                    <strong>{delGrupo.length} {delGrupo.length === 1 ? "rack" : "racks"}</strong>
                    <span className="muted">{c.nombre} · {numero(porcentaje, 1)}% del movimiento</span>
                  </div>
                );
              })}
            </div>

            <div className="abc-tabla" role="table" aria-label="Clasificación ABC por rack">
              <div className="abc-fila abc-encabezado" role="row">
                <span>Rack</span><span>Clase</span><span>Participación</span><span>Unidades</span><span>Acum.</span>
              </div>
              {filas.map((f) => (
                <div key={f.rack_id} className="abc-fila" role="row">
                  <span className="mono">{f.rack_id}</span>
                  <span className="clase-chip" data-clase={f.clase}>{f.clase}</span>
                  <span className="abc-barra" title={`${numero(f.porcentaje_del_total, 1)}% del total`}>
                    <span data-clase={f.clase} style={{ width: `${(f.porcentaje_del_total / maximo) * 100}%` }} />
                  </span>
                  <span className="mono">{numero(f.total_recogidas)}</span>
                  <span className="mono">{numero(f.porcentaje_acumulado, 1)}%</span>
                </div>
              ))}
            </div>
          </>
        )}
      </section>

      <div className="analisis-columna">
        {/* ---------- Predicción de demanda ---------- */}
        <section className="card">
          <header>
            <h2 className="card-title">Predicción de demanda</h2>
            <p className="card-sub">Regresión lineal sobre el historial diario del rack.</p>
          </header>

          <label className="campo-rack">
            <span className="field-label">Rack</span>
            <select className="select" value={rack} onChange={(e) => setRack(e.target.value)} disabled={filas.length === 0}>
              {filas.map((f) => (
                <option key={f.rack_id} value={f.rack_id}>{f.rack_id} · clase {f.clase}</option>
              ))}
            </select>
          </label>

          {pred.error && <p className="aviso-error">{pred.error}</p>}
          {pred.cargando && !pred.datos && <p className="muted">Calculando…</p>}

          {pred.datos && (
            <>
              <div className="kpis">
                <div className="kpi">
                  <span className="kpi-valor">{numero(pred.datos.promedio_historico_diario, 1)}</span>
                  <span className="kpi-etiqueta">unidades/día (promedio)</span>
                </div>
                <div className="kpi">
                  <span className="kpi-valor">{numero(pred.datos.prediccion_proxima_semana, 0)}</span>
                  <span className="kpi-etiqueta">unidades próxima semana</span>
                </div>
                <div className="kpi">
                  <span className="kpi-valor" data-tendencia={pred.datos.tendencia}>
                    {TENDENCIAS[pred.datos.tendencia]?.icono}
                  </span>
                  <span className="kpi-etiqueta">{TENDENCIAS[pred.datos.tendencia]?.texto ?? pred.datos.tendencia}</span>
                </div>
              </div>
              <Sparkline historico={pred.datos.serie_reciente} prediccion={pred.datos.prediccion_diaria} />
            </>
          )}
        </section>

        {/* ---------- Recomendaciones de reubicación ---------- */}
        <section className="card">
          <header>
            <h2 className="card-title">Recomendaciones de reubicación</h2>
            <p className="card-sub">Racks de alta rotación lejos de la salida que podrían moverse a un rack vacío más cercano.</p>
          </header>

          {reco.cargando && <p className="muted">Cargando…</p>}
          {reco.error && <p className="aviso-error">{reco.error}</p>}

          {reco.datos && (
            <>
              <p className="resumen-agente">{reco.datos.resumen_agente}</p>
              <ul className="reco-lista">
                {reco.datos.recomendaciones.map((r) => (
                  <li key={`${r.rack_actual}-${r.rack_sugerido}`} className="reco">
                    <div className="reco-ruta">
                      <span className="mono">{r.rack_actual}</span>
                      <span aria-hidden="true">→</span>
                      <span className="mono">{r.rack_sugerido}</span>
                      <span className="reco-ahorro">−{r.ahorro_distancia} u. por viaje</span>
                    </div>
                    <p className="reco-texto">{r.explicacion}</p>
                    <p className="muted">
                      Distancia a la salida: {r.distancia_actual} → {r.distancia_sugerida}
                    </p>
                  </li>
                ))}
              </ul>
            </>
          )}
        </section>
      </div>
    </div>
  );
}
