"""Análisis de inventario: clasificación ABC y predicción de demanda."""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, Security
from sqlalchemy.orm import Session

from agente_espacio import calcular_clasificacion_abc
from database import get_db
from models import HistorialPicking
from routers.etiquetas import TAG_ANALISIS
from schemas import ClasificacionABC, PrediccionDemandaDTO
from seguridad import requerir_autenticacion
from servicios.demanda import predecir_demanda

router = APIRouter(prefix="/api/v1", tags=[TAG_ANALISIS], dependencies=[Security(requerir_autenticacion)])

MINIMO_DIAS_HISTORIAL = 7
DIAS_SERIE_RECIENTE = 30


@router.get("/analisis-abc", response_model=List[ClasificacionABC], summary="Clasificación ABC")
def clasificacion_abc(db: Session = Depends(get_db)):
    """Clasifica cada rack en A, B o C según su participación acumulada en las unidades recogidas
    (A = hasta ~80% del movimiento, B = hasta ~95%, C = el resto)."""
    df = calcular_clasificacion_abc(db)
    if df.empty:
        raise HTTPException(
            status_code=404, detail="No hay historial de picking cargado todavía. Ejecuta seed_historial.py."
        )
    return [
        ClasificacionABC(
            rack_id=fila.rack_id,
            total_recogidas=int(fila.total),
            porcentaje_del_total=float(fila.porcentaje_del_total),
            porcentaje_acumulado=float(fila.porcentaje_acumulado),
            clase=fila.clase,
        )
        for fila in df.itertuples()
    ]


@router.get("/prediccion-demanda/{rack_id}", response_model=PrediccionDemandaDTO, summary="Predicción de demanda")
def prediccion_demanda(rack_id: str, db: Session = Depends(get_db)):
    """Predice la demanda de la próxima semana de un rack con una regresión lineal sobre su historial diario."""
    historial = (
        db.query(HistorialPicking).filter(HistorialPicking.rack_id == rack_id).order_by(HistorialPicking.fecha).all()
    )
    if len(historial) < MINIMO_DIAS_HISTORIAL:
        raise HTTPException(
            status_code=404,
            detail=f"No hay suficiente historial para '{rack_id}' (mínimo {MINIMO_DIAS_HISTORIAL} días).",
        )

    fechas = [h.fecha for h in historial]
    cantidades = [h.cantidad_recogida for h in historial]
    resultado = predecir_demanda(fechas, cantidades)

    return PrediccionDemandaDTO(
        rack_id=rack_id,
        promedio_historico_diario=resultado["promedio_diario"],
        prediccion_proxima_semana=resultado["prediccion_semana"],
        tendencia=resultado["tendencia"],
        serie_reciente=[int(c) for c in cantidades[-DIAS_SERIE_RECIENTE:]],
        prediccion_diaria=resultado["prediccion_diaria"],
    )
