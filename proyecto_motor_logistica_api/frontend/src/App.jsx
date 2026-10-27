import { useEffect, useState, useCallback } from "react";
import { useAuth } from "./auth";
import { fetchUbicaciones, optimizarRuta, fetchMensajesAgente } from "./api";
import SelectionPanel from "./components/SelectionPanel";
import ShelfGrid from "./components/ShelfGrid";
import LoginGate from "./components/LoginGate";
import RackModal from "./components/RackModal";
import AgentPanel from "./components/AgentPanel";
import AnalisisView from "./components/AnalisisView";
import "./App.css";
import "./paquetes.css";
import "./analisis.css";

export default function App() {
  const { autenticado, usuario, local, obtenerToken, cerrarSesion } = useAuth();

  const [vista, setVista] = useState("almacen"); // "almacen" | "analisis"
  const [ubicaciones, setUbicaciones] = useState([]);
  const [origenId, setOrigenId] = useState("");
  const [seleccionados, setSeleccionados] = useState([]);
  const [resultado, setResultado] = useState(null);
  const [cargando, setCargando] = useState(false);
  const [error, setError] = useState(null);

  // Ventana emergente de paquetes (guarda solo el id del rack abierto)
  const [rackAbierto, setRackAbierto] = useState(null);

  // Asistente
  const [rol, setRol] = useState("empleado");
  const [agente, setAgente] = useState(null);
  const [agenteCargando, setAgenteCargando] = useState(false);
  const [agenteError, setAgenteError] = useState(null);

  const cargarAgente = useCallback(async () => {
    setAgenteCargando(true);
    try {
      const token = await obtenerToken();
      setAgente(await fetchMensajesAgente(rol, token));
      setAgenteError(null);
    } catch (e) {
      setAgenteError(e.message);
    } finally {
      setAgenteCargando(false);
    }
  }, [obtenerToken, rol]);

  // Carga inicial de racks
  useEffect(() => {
    if (!autenticado) return;
    obtenerToken()
      .then((token) => fetchUbicaciones(token))
      .then((data) => {
        setUbicaciones(data);
        const depot = data.find((u) => u.id === "DEPOT");
        setOrigenId(depot ? depot.id : data[0]?.id ?? "");
      })
      .catch((e) => setError(e.message));
  }, [autenticado, obtenerToken]);

  // Mensajes del asistente: al entrar y cada vez que se cambia de rol
  useEffect(() => {
    if (autenticado) cargarAgente();
  }, [autenticado, cargarAgente]);

  // Después de agregar o eliminar un paquete: actualiza contadores y mensajes
  async function refrescarDatos() {
    try {
      const token = await obtenerToken();
      setUbicaciones(await fetchUbicaciones(token));
    } catch (e) {
      setError(e.message);
    }
    cargarAgente();
  }

  const cerrarModal = useCallback(() => setRackAbierto(null), []);

  function toggleRack(id) {
    if (id === origenId) return;
    setResultado(null);
    setSeleccionados((prev) =>
      prev.includes(id) ? prev.filter((r) => r !== id) : [...prev, id]
    );
  }

  async function handleSubmit() {
    setCargando(true);
    setError(null);
    try {
      const token = await obtenerToken();
      const data = await optimizarRuta(origenId, seleccionados, token);
      setResultado(data);
    } catch (e) {
      setError(e.message);
      setResultado(null);
    } finally {
      setCargando(false);
    }
  }

  if (!autenticado) {
    return <LoginGate />;
  }

  const ordenRuta = resultado
    ? new Map(resultado.secuencia_optima.map((s, i) => [s.id, i]))
    : undefined;

  // Se busca el rack en la lista actual para que su contador se actualice en vivo
  const rackModal = rackAbierto ? ubicaciones.find((u) => u.id === rackAbierto) : null;
  const enAlmacen = vista === "almacen";

  return (
    <>
      <div className={`app ${enAlmacen ? "" : "app-analisis"}`}>
        {enAlmacen && (
          <SelectionPanel
            ubicaciones={ubicaciones}
            origenId={origenId}
            setOrigenId={setOrigenId}
            seleccionados={seleccionados}
            onSubmit={handleSubmit}
            cargando={cargando}
          />
        )}

        <main className="main">
          <div className="topbar">
            <nav className="tabs" aria-label="Vistas">
              <button
                type="button"
                className={`tab ${enAlmacen ? "tab-activa" : ""}`}
                onClick={() => setVista("almacen")}
              >
                Almacén
              </button>
              <button
                type="button"
                className={`tab ${!enAlmacen ? "tab-activa" : ""}`}
                onClick={() => setVista("analisis")}
              >
                Análisis
              </button>
            </nav>
            <div className="topbar-usuario">
              {!local && <span className="user-chip">{usuario}</span>}
              {local ? (
                <span className="local-chip" title="La autenticación está desactivada (solo desarrollo local)">
                  Modo local
                </span>
              ) : (
                <button className="link-btn" onClick={cerrarSesion}>
                  Cerrar sesión
                </button>
              )}
            </div>
          </div>

          {error && <div className="error-banner">{error}</div>}

          {enAlmacen ? (
            <>
              {resultado && (
                <div className="stats-bar">
                  <div className="stat">
                    <span className="stat-value">{resultado.distancia_total_unidades}</span>
                    <span className="stat-label">unidades de distancia</span>
                  </div>
                  <div className="stat">
                    <span className="stat-value">{resultado.secuencia_optima.length - 2}</span>
                    <span className="stat-label">estantes visitados</span>
                  </div>
                </div>
              )}

              <div className="content-row">
                <ShelfGrid
                  ubicaciones={ubicaciones}
                  seleccionados={seleccionados}
                  toggleRack={toggleRack}
                  ordenRuta={ordenRuta}
                  onInfo={(rack) => setRackAbierto(rack.id)}
                />
                <AgentPanel
                  rol={rol}
                  setRol={setRol}
                  datos={agente}
                  cargando={agenteCargando}
                  error={agenteError}
                />
              </div>
            </>
          ) : (
            <AnalisisView obtenerToken={obtenerToken} />
          )}
        </main>
      </div>

      {rackModal && (
        <RackModal
          rack={rackModal}
          obtenerToken={obtenerToken}
          onCerrar={cerrarModal}
          onCambio={refrescarDatos}
        />
      )}
    </>
  );
}
