// Gráfica simple: demanda de los últimos días (línea sólida) y pronóstico (línea punteada).
export default function Sparkline({ historico, prediccion }) {
  const ancho = 520;
  const alto = 150;
  const m = { izq: 8, der: 8, sup: 14, inf: 24 };
  const total = historico.length + prediccion.length;
  if (historico.length < 2 || prediccion.length < 1) return null;

  const maximo = Math.max(1, ...historico, ...prediccion);
  const x = (i) => m.izq + (i / (total - 1)) * (ancho - m.izq - m.der);
  const y = (v) => m.sup + (1 - v / maximo) * (alto - m.sup - m.inf);
  const linea = (serie, desde) =>
    serie.map((v, i) => `${x(desde + i).toFixed(1)},${y(v).toFixed(1)}`).join(" ");

  const ultimo = historico[historico.length - 1];
  const corte = x(historico.length - 1);

  return (
    <svg
      viewBox={`0 0 ${ancho} ${alto}`}
      className="spark"
      role="img"
      aria-label={`Demanda de los últimos ${historico.length} días y pronóstico de los próximos ${prediccion.length}`}
    >
      <line x1={m.izq} x2={ancho - m.der} y1={alto - m.inf} y2={alto - m.inf} className="spark-eje" />
      <line x1={corte} x2={corte} y1={m.sup} y2={alto - m.inf} className="spark-corte" />
      <polyline points={linea(historico, 0)} className="spark-hist" />
      <polyline points={linea([ultimo, ...prediccion], historico.length - 1)} className="spark-pred" />
      <text x={m.izq} y={alto - 6} className="spark-texto">Últimos {historico.length} días</text>
      <text x={ancho - m.der} y={alto - 6} className="spark-texto" textAnchor="end">
        Próximos {prediccion.length} días
      </text>
      <text x={m.izq} y={m.sup - 2} className="spark-texto">máx. {Math.round(maximo)} u./día</text>
    </svg>
  );
}
