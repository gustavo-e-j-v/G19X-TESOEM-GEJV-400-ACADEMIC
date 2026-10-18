const API_BASE = "http://127.0.0.1:8000";

function authHeaders(token) {
  return token ? { Authorization: `Bearer ${token}` } : {};
}

// Devuelve el JSON de la respuesta (o null si es 204) y, si falla, lanza un
// Error con el motivo que mandó la API (campo "detail") para mostrarlo en pantalla.
async function manejarRespuesta(res, mensajeGenerico) {
  if (!res.ok) {
    const cuerpo = await res.json().catch(() => null);
    const d = cuerpo?.detail;
    const texto =
      typeof d === "string" ? d : Array.isArray(d) ? d.map((e) => e.msg).join("; ") : null;
    throw new Error(texto || mensajeGenerico);
  }
  return res.status === 204 ? null : res.json();
}

// ---------- Ubicaciones y rutas ----------

export async function fetchUbicaciones(token) {
  const res = await fetch(`${API_BASE}/api/v1/ubicaciones`, { headers: authHeaders(token) });
  return manejarRespuesta(res, "No se pudieron cargar las ubicaciones del almacén.");
}

export async function optimizarRuta(origenId, racksIds, token) {
  const res = await fetch(`${API_BASE}/api/v1/optimizar-ruta-bd`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...authHeaders(token) },
    body: JSON.stringify({ origen_id: origenId, racks_ids: racksIds }),
  });
  return manejarRespuesta(res, "No se pudo calcular la ruta.");
}

// ---------- Paquetes por rack ----------

export async function fetchPaquetes(rackId, token) {
  const res = await fetch(`${API_BASE}/api/v1/racks/${encodeURIComponent(rackId)}/paquetes`, {
    headers: authHeaders(token),
  });
  return manejarRespuesta(res, "No se pudieron cargar los paquetes del rack.");
}

export async function crearPaquete(rackId, datos, token) {
  const res = await fetch(`${API_BASE}/api/v1/racks/${encodeURIComponent(rackId)}/paquetes`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...authHeaders(token) },
    body: JSON.stringify(datos),
  });
  return manejarRespuesta(res, "No se pudo guardar el paquete.");
}

export async function eliminarPaquete(paqueteId, token) {
  const res = await fetch(`${API_BASE}/api/v1/paquetes/${paqueteId}`, {
    method: "DELETE",
    headers: authHeaders(token),
  });
  return manejarRespuesta(res, "No se pudo eliminar el paquete.");
}

// ---------- Asistente ----------

export async function fetchMensajesAgente(rol, token) {
  const res = await fetch(`${API_BASE}/api/v1/mensajes-agente?rol=${encodeURIComponent(rol)}`, {
    headers: authHeaders(token),
  });
  return manejarRespuesta(res, "No se pudieron cargar los mensajes del asistente.");
}
