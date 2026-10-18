import { useEffect, useState, useCallback } from "react";
import { useMsal, useIsAuthenticated } from "@azure/msal-react";
import { fetchUbicaciones, optimizarRuta, fetchMensajesAgente } from "./api";
import { loginRequest } from "./authConfig";
import SelectionPanel from "./components/SelectionPanel";
import ShelfGrid from "./components/ShelfGrid";
import LoginGate from "./components/LoginGate";
import RackModal from "./components/RackModal";
import AgentPanel from "./components/AgentPanel";
import "./App.css";
import "./paquetes.css";

export default function App() {
  const isAuthenticated = useIsAuthenticated();
  const { instance, accounts } = useMsal();

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

  // Pide un token de acceso silenciosamente (sin volver a mostrar login si ya hay sesión).
  const obtenerToken = useCallback(async () => {
    const cuenta = accounts[0];
    const respuesta = await instance.acquireTokenSilent({
      ...loginRequest,
      account: cuenta,
    });
    return respuesta.accessToken;
  }, [instance, accounts]);

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
    if (!isAuthenticated) return;
    obtenerToken()
      .then((token) => fetchUbicaciones(token))
      .then((data) => {
        setUbicaciones(data);
        const depot = data.find((u) => u.id === "DEPOT");
        setOrigenId(depot ? depot.id : data[0]?.id ?? "");
      })
      .catch((e) => setError(e.message));
  }, [isAuthenticated, obtenerToken]);

  // Mensajes del asistente: al entrar y cada vez que se cambia de rol
  useEffect(() => {
    if (isAuthenticated) cargarAgente();
  }, [isAuthenticated, cargarAgente]);

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

  if (!isAuthenticated) {
    return <LoginGate />;
  }

  const ordenRuta = resultado
    ? new Map(resultado.secuencia_optima.map((s, i) => [s.id, i]))
    : undefined;

  // Se busca el rack en la lista actual para que su contador se actualice en vivo
  const rackModal = rackAbierto ? ubicaciones.find((u) => u.id === rackAbierto) : null;

  return (
    <>
      <div className="app">
        <SelectionPanel
          ubicaciones={ubicaciones}
          origenId={origenId}
          setOrigenId={setOrigenId}
          seleccionados={seleccionados}
          onSubmit={handleSubmit}
          cargando={cargando}
        />

        <main className="main">
          <div className="topbar">
            <span className="user-chip">{accounts[0]?.username}</span>
            <button className="link-btn" onClick={() => instance.logoutRedirect()}>
              Cerrar sesión
            </button>
          </div>

          {error && <div className="error-banner">{error}</div>}

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
