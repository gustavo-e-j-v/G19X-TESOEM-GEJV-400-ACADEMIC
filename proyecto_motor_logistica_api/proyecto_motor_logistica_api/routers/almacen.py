"""Racks del almacén y ruta óptima de picking."""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, Security
from sqlalchemy import func
from sqlalchemy.orm import Session

from database import get_db
from models import Paquete, UbicacionRack
from routers.etiquetas import TAG_ALMACEN
from schemas import PeticionPickingIDs, RespuestaRuta, UbicacionDTO
from seguridad import requerir_autenticacion
from servicios.rutas import resolver_tsp

router = APIRouter(prefix="/api/v1", tags=[TAG_ALMACEN], dependencies=[Security(requerir_autenticacion)])


@router.get("/ubicaciones", response_model=List[UbicacionDTO], summary="Listar ubicaciones")
def listar_ubicaciones(db: Session = Depends(get_db)):
    """Devuelve todos los racks activos, con su número de paquetes y la fecha de entrega más cercana."""
    registros = db.query(UbicacionRack).filter(UbicacionRack.activo == True).all()  # noqa: E712

    # Paquetes por rack y fecha de entrega más cercana, en una sola consulta
    resumen = {
        rack_id: (cantidad, fecha)
        for rack_id, cantidad, fecha in db.query(
            Paquete.rack_id, func.count(Paquete.id), func.min(Paquete.fecha_entrega)
        )
        .group_by(Paquete.rack_id)
        .all()
    }

    return [
        UbicacionDTO(
            id=r.id,
            x=r.x,
            y=r.y,
            ocupado=r.ocupado,
            num_paquetes=resumen.get(r.id, (0, None))[0],
            fecha_entrega_mas_proxima=resumen.get(r.id, (0, None))[1],
        )
        for r in registros
    ]


@router.post("/optimizar-ruta-bd", response_model=RespuestaRuta, summary="Calcular ruta óptima")
def optimizar_ruta_desde_bd(peticion: PeticionPickingIDs, db: Session = Depends(get_db)):
    """Calcula el orden más corto para visitar los racks indicados, saliendo y regresando al origen."""
    # Sin repetidos y sin incluir el origen como destino
    destinos = [r for r in dict.fromkeys(peticion.racks_ids) if r != peticion.origen_id]
    if not destinos:
        raise HTTPException(status_code=400, detail="Indica al menos un rack distinto del punto de salida.")

    registros = db.query(UbicacionRack).filter(UbicacionRack.id.in_([peticion.origen_id, *destinos])).all()
    mapa = {r.id: UbicacionDTO(id=r.id, x=r.x, y=r.y, ocupado=r.ocupado) for r in registros}

    if peticion.origen_id not in mapa:
        raise HTTPException(status_code=404, detail=f"El punto de origen '{peticion.origen_id}' no existe en la BD.")
    for rack_id in destinos:
        if rack_id not in mapa:
            raise HTTPException(status_code=404, detail=f"Ubicación o rack '{rack_id}' no encontrado en la BD.")

    puntos = [mapa[peticion.origen_id]] + [mapa[r] for r in destinos]
    try:
        orden, distancia = resolver_tsp(puntos)
    except ValueError as error:
        raise HTTPException(status_code=500, detail=str(error))

    return RespuestaRuta(secuencia_optima=[puntos[i] for i in orden], distancia_total_unidades=distancia)
