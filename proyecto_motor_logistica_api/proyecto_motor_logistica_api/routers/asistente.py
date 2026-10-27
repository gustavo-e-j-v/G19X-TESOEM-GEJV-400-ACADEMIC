"""Asistente: recomendaciones de reubicación y mensajes por rol."""

from typing import Literal

from fastapi import APIRouter, Depends, Security
from sqlalchemy.orm import Session

from agente_espacio import generar_recomendaciones
from agente_mensajes import generar_mensajes
from database import get_db
from routers.etiquetas import TAG_ASISTENTE
from schemas import MensajesAgenteDTO, RespuestaRecomendacionesDTO
from seguridad import requerir_autenticacion

router = APIRouter(prefix="/api/v1", tags=[TAG_ASISTENTE], dependencies=[Security(requerir_autenticacion)])


@router.get(
    "/recomendaciones-espacio", response_model=RespuestaRecomendacionesDTO, summary="Recomendaciones de espacio"
)
def recomendaciones_espacio(db: Session = Depends(get_db)):
    """Analiza clasificación ABC, ocupación y distancias, y recomienda reubicaciones para reducir el recorrido."""
    return RespuestaRecomendacionesDTO(**generar_recomendaciones(db))


@router.get("/mensajes-agente", response_model=MensajesAgenteDTO, summary="Mensajes del asistente")
def mensajes_agente(rol: Literal["encargado", "empleado"] = "empleado", db: Session = Depends(get_db)):
    """Mensajes de apoyo y consejos según el rol, más el paquete con la entrega más próxima."""
    return MensajesAgenteDTO(**generar_mensajes(db, rol))
