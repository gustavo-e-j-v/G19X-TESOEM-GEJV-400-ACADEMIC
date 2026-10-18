import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from datetime import date, timedelta
from typing import List, Optional, Literal

from fastapi import FastAPI, HTTPException, Depends, Security, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.openapi.docs import get_swagger_ui_oauth2_redirect_html
from pydantic import BaseModel, Field, ConfigDict
from sqlalchemy.orm import Session
from sqlalchemy import func

import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression

from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp

from fastapi_azure_auth import SingleTenantAzureAuthorizationCodeBearer

from database import get_db, engine, Base
from models import UbicacionRack, HistorialPicking, Paquete
from agente_espacio import generar_recomendaciones
from agente_mensajes import generar_mensajes, paquete_a_dict
from docs_tema import construir_docs_html

# --- Configuración de Microsoft Entra ID ---
AZURE_TENANT_ID = os.getenv("AZURE_TENANT_ID", "fea7c33e-0fa3-43f3-aeb6-d5d6a25c855c")
AZURE_API_CLIENT_ID = os.getenv("AZURE_API_CLIENT_ID", "1fc0a49f-ce9e-43c1-a35b-dea22b55d8c5")

azure_scheme = SingleTenantAzureAuthorizationCodeBearer(
    app_client_id=AZURE_API_CLIENT_ID,
    tenant_id=AZURE_TENANT_ID,
    scopes={
        f"api://{AZURE_API_CLIENT_ID}/access_as_user": "access_as_user",
    },
    allow_guest_users=True,
)

# Secciones de la documentación (cada una es un contenedor en /docs)
TAG_ALMACEN = "Almacén y rutas"
TAG_PAQUETES = "Paquetes"
TAG_ANALISIS = "Análisis de inventario"
TAG_ASISTENTE = "Asistente"

ETIQUETAS = [
    {"name": TAG_ALMACEN, "description": "Racks del almacén y cálculo de la ruta óptima de picking."},
    {"name": TAG_PAQUETES, "description": "Paquetes de cada rack con su fecha de entrega."},
    {"name": TAG_ANALISIS, "description": "Clasificación ABC por rotación y predicción de demanda."},
    {"name": TAG_ASISTENTE, "description": "Mensajes de apoyo por rol y recomendaciones de reubicación."},
]

app = FastAPI(
    title="Motor de Optimización Logística",
    version="1.3.1",
    description=(
        "Rutas de picking, paquetes por rack, análisis de inventario y asistente por rol. "
        "Todos los endpoints requieren iniciar sesión con Microsoft Entra ID."
    ),
    openapi_tags=ETIQUETAS,
    docs_url=None,  # /docs se sirve más abajo, con el tema propio (docs_tema.py)
    swagger_ui_oauth2_redirect_url="/oauth2-redirect",
    swagger_ui_init_oauth={
        "usePkceWithAuthorizationCodeGrant": True,
        "clientId": AZURE_API_CLIENT_ID,
        "scopes": f"api://{AZURE_API_CLIENT_ID}/access_as_user",
    },
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/docs", include_in_schema=False)
async def documentacion():
    return HTMLResponse(construir_docs_html(app))


@app.get("/oauth2-redirect", include_in_schema=False)
async def oauth2_redirect():
    # Página a la que Microsoft regresa tras iniciar sesión desde el botón Authorize
    return get_swagger_ui_oauth2_redirect_html()


@app.on_event("startup")
async def cargar_configuracion_azure():
    await azure_scheme.openid_config.load_config()

Base.metadata.create_all(bind=engine)


# ==========================================================================
# Modelos (DTOs)
# ==========================================================================

class UbicacionDTO(BaseModel):
    id: str
    x: int
    y: int
    ocupado: bool = False
    num_paquetes: int = 0
    fecha_entrega_mas_proxima: Optional[date] = None

    model_config = ConfigDict(from_attributes=True)

class PeticionPickingIDs(BaseModel):
    origen_id: str = Field(..., description="ID del punto de salida")
    racks_ids: List[str] = Field(..., description="Lista de IDs de racks a visitar")

class RespuestaRuta(BaseModel):
    secuencia_optima: List[UbicacionDTO]
    distancia_total_unidades: int

class ClasificacionABC(BaseModel):
    rack_id: str
    total_recogidas: int
    porcentaje_del_total: float
    porcentaje_acumulado: float
    clase: str  # "A", "B" o "C"

class PrediccionDemandaDTO(BaseModel):
    rack_id: str
    promedio_historico_diario: float
    prediccion_proxima_semana: float
    tendencia: str  # "creciente", "estable" o "decreciente"

class RecomendacionEspacioDTO(BaseModel):
    rack_actual: str
    clase: str
    distancia_actual: int
    rack_sugerido: str
    distancia_sugerida: int
    ahorro_distancia: int
    explicacion: str

class RespuestaRecomendacionesDTO(BaseModel):
    resumen_agente: str
    recomendaciones: List[RecomendacionEspacioDTO]

class PaqueteCrearDTO(BaseModel):
    codigo: str = Field(..., min_length=1, max_length=60, description="Código o guía del paquete")
    descripcion: Optional[str] = Field(None, max_length=200)
    fecha_entrega: date

class PaqueteDTO(BaseModel):
    id: int
    codigo: str
    descripcion: Optional[str] = None
    rack_id: str
    fecha_entrega: date
    dias_restantes: int  # negativo = ya venció

class MensajeAgenteDTO(BaseModel):
    tipo: str   # urgente | aviso | consejo | info
    texto: str

class MensajesAgenteDTO(BaseModel):
    rol: str
    resumen: str
    paquete_mas_proximo: Optional[PaqueteDTO] = None
    mensajes: List[MensajeAgenteDTO]


# ==========================================================================
# Utilidades del algoritmo de rutas (TSP)
# ==========================================================================

def calcular_distancia_manhattan(p1: UbicacionDTO, p2: UbicacionDTO) -> int:
    return abs(p1.x - p2.x) + abs(p1.y - p2.y)

def resolver_tsp(locations: List[UbicacionDTO]) -> tuple[List[int], int]:
    num_puntos = len(locations)
    distance_matrix = [
        [calcular_distancia_manhattan(locations[i], locations[j]) for j in range(num_puntos)]
        for i in range(num_puntos)
    ]

    manager = pywrapcp.RoutingIndexManager(num_puntos, 1, 0)
    routing = pywrapcp.RoutingModel(manager)

    def distance_callback(from_index, to_index):
        from_node = manager.IndexToNode(from_index)
        to_node = manager.IndexToNode(to_index)
        return distance_matrix[from_node][to_node]

    transit_callback_index = routing.RegisterTransitCallback(distance_callback)
    routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

    search_parameters = pywrapcp.DefaultRoutingSearchParameters()
    search_parameters.first_solution_strategy = routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC

    solution = routing.SolveWithParameters(search_parameters)
    if not solution:
        raise ValueError("No se pudo calcular una ruta de picking.")

    index = routing.Start(0)
    route_indices = []
    total_distance = 0

    while not routing.IsEnd(index):
        node_index = manager.IndexToNode(index)
        route_indices.append(node_index)
        previous_index = index
        index = solution.Value(routing.NextVar(index))
        total_distance += routing.GetArcCostForVehicle(previous_index, index, 0)

    route_indices.append(manager.IndexToNode(index))
    return route_indices, total_distance


# ==========================================================================
# Endpoints: ubicaciones y rutas (ya existentes)
# ==========================================================================

@app.get("/api/v1/ubicaciones", tags=[TAG_ALMACEN], summary="Listar ubicaciones", response_model=List[UbicacionDTO], dependencies=[Security(azure_scheme)])
def listar_ubicaciones(db: Session = Depends(get_db)):
    registros = db.query(UbicacionRack).filter(UbicacionRack.activo == True).all()

    # Paquetes por rack y fecha de entrega más cercana, en una sola consulta.
    resumen_paquetes = {
        rack_id: (cantidad, fecha)
        for rack_id, cantidad, fecha in db.query(
            Paquete.rack_id, func.count(Paquete.id), func.min(Paquete.fecha_entrega)
        ).group_by(Paquete.rack_id).all()
    }

    return [
        UbicacionDTO(
            id=r.id, x=r.x, y=r.y, ocupado=r.ocupado,
            num_paquetes=resumen_paquetes.get(r.id, (0, None))[0],
            fecha_entrega_mas_proxima=resumen_paquetes.get(r.id, (0, None))[1],
        )
        for r in registros
    ]


@app.post("/api/v1/optimizar-ruta-bd", tags=[TAG_ALMACEN], summary="Calcular ruta óptima", response_model=RespuestaRuta, dependencies=[Security(azure_scheme)])
def optimizar_ruta_desde_bd(
    peticion: PeticionPickingIDs,
    db: Session = Depends(get_db)
):
    todos_los_ids = [peticion.origen_id] + peticion.racks_ids

    registros_bd = db.query(UbicacionRack).filter(UbicacionRack.id.in_(todos_los_ids)).all()
    mapa_racks = {r.id: UbicacionDTO(id=r.id, x=r.x, y=r.y, ocupado=r.ocupado) for r in registros_bd}

    if peticion.origen_id not in mapa_racks:
        raise HTTPException(status_code=404, detail=f"El punto de origen '{peticion.origen_id}' no existe en la BD.")

    puntos_a_visitar = [mapa_racks[peticion.origen_id]]
    for r_id in peticion.racks_ids:
        if r_id not in mapa_racks:
            raise HTTPException(status_code=404, detail=f"Ubicación o rack '{r_id}' no encontrado en PostgreSQL.")
        puntos_a_visitar.append(mapa_racks[r_id])

    indices_ordenados, distancia_total = resolver_tsp(puntos_a_visitar)
    secuencia_ordenada = [puntos_a_visitar[idx] for idx in indices_ordenados]

    return RespuestaRuta(
        secuencia_optima=secuencia_ordenada,
        distancia_total_unidades=distancia_total
    )


# ==========================================================================
# Endpoints nuevos: clasificación ABC y predicción de demanda
# ==========================================================================

@app.get("/api/v1/analisis-abc", tags=[TAG_ANALISIS], summary="Clasificación ABC", response_model=List[ClasificacionABC], dependencies=[Security(azure_scheme)])
def clasificacion_abc(db: Session = Depends(get_db)):
    """Clasifica cada rack en A, B o C según su participación acumulada en el
    total de unidades recogidas históricamente (regla clásica de inventarios:
    A = ~80% del movimiento, B = siguiente ~15%, C = el 5% restante)."""

    resultados = (
        db.query(HistorialPicking.rack_id, func.sum(HistorialPicking.cantidad_recogida).label("total"))
        .group_by(HistorialPicking.rack_id)
        .all()
    )

    if not resultados:
        raise HTTPException(status_code=404, detail="No hay historial de picking cargado todavía. Corre seed_historial.py.")

    df = pd.DataFrame(resultados, columns=["rack_id", "total"]).sort_values("total", ascending=False)
    total_general = df["total"].sum()

    df["porcentaje_del_total"] = (df["total"] / total_general * 100).round(2)
    df["porcentaje_acumulado"] = df["porcentaje_del_total"].cumsum().round(2)

    def asignar_clase(pct_acumulado: float) -> str:
        if pct_acumulado <= 80:
            return "A"
        elif pct_acumulado <= 95:
            return "B"
        return "C"

    df["clase"] = df["porcentaje_acumulado"].apply(asignar_clase)

    return [
        ClasificacionABC(
            rack_id=row.rack_id,
            total_recogidas=int(row.total),
            porcentaje_del_total=row.porcentaje_del_total,
            porcentaje_acumulado=row.porcentaje_acumulado,
            clase=row.clase,
        )
        for row in df.itertuples()
    ]


@app.get(
    "/api/v1/prediccion-demanda/{rack_id}", tags=[TAG_ANALISIS], summary="Predicción de demanda",
    response_model=PrediccionDemandaDTO,
    dependencies=[Security(azure_scheme)],
)
def prediccion_demanda(rack_id: str, db: Session = Depends(get_db)):
    """Predice la demanda de la próxima semana para un rack, ajustando una
    regresión lineal sobre su historial diario de recolecciones."""

    historial = (
        db.query(HistorialPicking)
        .filter(HistorialPicking.rack_id == rack_id)
        .order_by(HistorialPicking.fecha)
        .all()
    )

    if len(historial) < 7:
        raise HTTPException(
            status_code=404,
            detail=f"No hay suficiente historial para '{rack_id}' (mínimo 7 días). Corre seed_historial.py.",
        )

    fechas = [h.fecha for h in historial]
    cantidades = np.array([h.cantidad_recogida for h in historial])
    dias_indice = np.array([(f - fechas[0]).days for f in fechas]).reshape(-1, 1)

    modelo = LinearRegression()
    modelo.fit(dias_indice, cantidades)

    ultimo_dia = dias_indice[-1][0]
    proximos_7_dias = np.arange(ultimo_dia + 1, ultimo_dia + 8).reshape(-1, 1)
    prediccion = modelo.predict(proximos_7_dias)
    prediccion_semana = max(0, float(prediccion.sum()))

    pendiente = modelo.coef_[0]
    if pendiente > 0.05:
        tendencia = "creciente"
    elif pendiente < -0.05:
        tendencia = "decreciente"
    else:
        tendencia = "estable"

    return PrediccionDemandaDTO(
        rack_id=rack_id,
        promedio_historico_diario=round(float(cantidades.mean()), 2),
        prediccion_proxima_semana=round(prediccion_semana, 2),
        tendencia=tendencia,
    )


@app.get(
    "/api/v1/recomendaciones-espacio", tags=[TAG_ASISTENTE], summary="Recomendaciones de espacio",
    response_model=RespuestaRecomendacionesDTO,
    dependencies=[Security(azure_scheme)],
)
def recomendaciones_espacio(db: Session = Depends(get_db)):
    """Agente que analiza clasificación ABC + ocupación + distancias y
    recomienda reubicaciones para reducir el recorrido de picking."""
    resultado = generar_recomendaciones(db)
    return RespuestaRecomendacionesDTO(**resultado)


# ==========================================================================
# Paquetes por rack y mensajes del asistente
# ==========================================================================

def _obtener_rack_o_404(db: Session, rack_id: str) -> UbicacionRack:
    rack = db.query(UbicacionRack).filter(UbicacionRack.id == rack_id).first()
    if rack is None:
        raise HTTPException(status_code=404, detail=f"El rack '{rack_id}' no existe.")
    return rack


@app.get("/api/v1/racks/{rack_id}/paquetes", tags=[TAG_PAQUETES], summary="Listar paquetes de un rack", response_model=List[PaqueteDTO], dependencies=[Security(azure_scheme)])
def listar_paquetes_rack(rack_id: str, db: Session = Depends(get_db)):
    """Paquetes de un rack, del que se entrega primero al que se entrega al final."""
    _obtener_rack_o_404(db, rack_id)
    paquetes = (
        db.query(Paquete)
        .filter(Paquete.rack_id == rack_id)
        .order_by(Paquete.fecha_entrega, Paquete.id)
        .all()
    )
    return [PaqueteDTO(**paquete_a_dict(p)) for p in paquetes]


@app.post(
    "/api/v1/racks/{rack_id}/paquetes", tags=[TAG_PAQUETES], summary="Registrar paquete",
    response_model=PaqueteDTO,
    status_code=201,
    dependencies=[Security(azure_scheme)],
)
def crear_paquete(rack_id: str, datos: PaqueteCrearDTO, db: Session = Depends(get_db)):
    """Registra un paquete en un rack (datos capturados por la persona)."""
    if rack_id == "DEPOT":
        raise HTTPException(status_code=400, detail="El punto de salida (DEPOT) no almacena paquetes.")
    rack = _obtener_rack_o_404(db, rack_id)

    codigo = datos.codigo.strip()
    if not codigo:
        raise HTTPException(status_code=422, detail="El código del paquete no puede estar vacío.")
    if db.query(Paquete).filter(Paquete.codigo == codigo).first():
        raise HTTPException(status_code=409, detail=f"Ya existe un paquete con el código '{codigo}'.")

    paquete = Paquete(
        codigo=codigo,
        descripcion=(datos.descripcion or "").strip() or None,
        rack_id=rack_id,
        fecha_entrega=datos.fecha_entrega,
    )
    db.add(paquete)
    rack.ocupado = True  # un rack con paquetes cuenta como lleno
    db.commit()
    db.refresh(paquete)
    return PaqueteDTO(**paquete_a_dict(paquete))


@app.delete(
    "/api/v1/paquetes/{paquete_id}", tags=[TAG_PAQUETES], summary="Eliminar paquete",
    status_code=204,
    response_class=Response,
    dependencies=[Security(azure_scheme)],
)
def eliminar_paquete(paquete_id: int, db: Session = Depends(get_db)):
    """Elimina un paquete (por ejemplo, cuando ya se entregó)."""
    paquete = db.query(Paquete).filter(Paquete.id == paquete_id).first()
    if paquete is None:
        raise HTTPException(status_code=404, detail=f"El paquete {paquete_id} no existe.")

    rack_id = paquete.rack_id
    db.delete(paquete)
    db.flush()

    restantes = db.query(func.count(Paquete.id)).filter(Paquete.rack_id == rack_id).scalar()
    if restantes == 0:
        rack = db.query(UbicacionRack).filter(UbicacionRack.id == rack_id).first()
        if rack is not None:
            rack.ocupado = False  # sin paquetes, el rack queda disponible
    db.commit()
    return Response(status_code=204)


@app.get("/api/v1/mensajes-agente", tags=[TAG_ASISTENTE], summary="Mensajes del asistente", response_model=MensajesAgenteDTO, dependencies=[Security(azure_scheme)])
def mensajes_agente(
    rol: Literal["encargado", "empleado"] = "empleado",
    db: Session = Depends(get_db),
):
    """Mensajes de apoyo y consejos según el rol, más el paquete con la entrega más próxima."""
    return MensajesAgenteDTO(**generar_mensajes(db, rol))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
