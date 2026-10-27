"""Modelos de datos (DTOs) de entrada y salida de la API."""

from datetime import date
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


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
    racks_ids: List[str] = Field(..., min_length=1, description="Lista de IDs de racks a visitar")


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
    serie_reciente: List[int] = []        # unidades recogidas en los últimos 30 días
    prediccion_diaria: List[float] = []   # pronóstico de los próximos 7 días


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
