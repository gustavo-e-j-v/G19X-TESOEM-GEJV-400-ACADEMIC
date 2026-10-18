import { formatearFecha, textoPaquetes } from "../formato";

// Agrupa las ubicaciones (excluyendo el DEPOT) por pasillo (coordenada y)
// y las ordena por posición dentro del pasillo (coordenada x).
function agruparPorPasillo(ubicaciones) {
  const racks = ubicaciones.filter((u) => u.id !== "DEPOT");
  const pasillos = new Map();

  for (const rack of racks) {
    if (!pasillos.has(rack.y)) pasillos.set(rack.y, []);
    pasillos.get(rack.y).push(rack);
  }

  return [...pasillos.entries()]
    .sort((a, b) => a[0] - b[0])
    .map(([y, items]) => [y, items.sort((a, b) => a.x - b.x)]);
}

export default function ShelfGrid({ ubicaciones, seleccionados, toggleRack, ordenRuta, onInfo }) {
  const pasillos = agruparPorPasillo(ubicaciones);

  // ordenRuta: Map de id -> número de parada, solo presente cuando ya hay resultado
  return (
    <div className="shelf-grid">
      {pasillos.map(([y, items]) => (
        <div className="shelf-row" key={y}>
          <span className="shelf-row-label">Pasillo {y}</span>
          <div className="shelf-row-items">
            {items.map((rack) => {
              const seleccionado = seleccionados.includes(rack.id);
              const numeroParada = ordenRuta?.get(rack.id);
              const n = rack.num_paquetes ?? 0;
              const titulo = [
                rack.id,
                textoPaquetes(n),
                rack.fecha_entrega_mas_proxima
                  ? `próxima entrega ${formatearFecha(rack.fecha_entrega_mas_proxima)}`
                  : null,
              ]
                .filter(Boolean)
                .join(" · ");

              return (
                <div className="shelf-cell" key={rack.id}>
                  <button
                    type="button"
                    onClick={() => toggleRack(rack.id)}
                    className={`shelf-tile ${rack.ocupado ? "shelf-full" : "shelf-empty"} ${
                      seleccionado ? "shelf-selected" : ""
                    }`}
                    title={titulo}
                  >
                    {numeroParada !== undefined && <span className="shelf-badge">{numeroParada}</span>}
                    <span className="shelf-id">{rack.id}</span>
                    <span className="shelf-count">{textoPaquetes(n)}</span>
                  </button>
                  <button
                    type="button"
                    className="shelf-info"
                    onClick={() => onInfo(rack)}
                    aria-label={`Ver y agregar paquetes de ${rack.id}`}
                    title="Ver y agregar paquetes"
                  >
                    i
                  </button>
                </div>
              );
            })}
          </div>
        </div>
      ))}

      <div className="shelf-legend">
        <span className="legend-item">
          <span className="legend-swatch legend-full" /> Lleno
        </span>
        <span className="legend-item">
          <span className="legend-swatch legend-empty" /> Vacío
        </span>
        <span className="legend-item">
          <span className="legend-swatch legend-selected" /> Seleccionado
        </span>
        <span className="legend-item">
          <span className="legend-info">i</span> Paquetes del rack
        </span>
      </div>
    </div>
  );
}
