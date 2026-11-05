"""Racks del almacén y ruta óptima de picking."""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, Security

from agente_mensajes import hoy_local
from sqlalchemy import func
from sqlalchemy.orm import Session

from database import get_db
from models import Paquete, UbicacionRack
from routers.etiquetas import TAG_ALMACEN
from schemas import (
    ConfirmarSurtidoDTO,
    ItemSurtidoDTO,
    PeticionPickingIDs,
    RespuestaRuta,
    RespuestaSurtidoDTO,
    UbicacionDTO,
)
from seguridad import requerir_autenticacion
from servicios.picking import RackNoEncontrado, RackNoSurtible, registrar_surtido
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


@router.post("/picking/ruta-surtida", response_model=RespuestaSurtidoDTO, summary="Confirmar ruta surtida")
def confirmar_ruta_surtida(datos: ConfirmarSurtidoDTO, db: Session = Depends(get_db)):
    """Confirma que una ruta ya se surtió: suma las unidades recogidas de cada rack al historial de picking.

    Con estos datos reales se calculan la clasificación ABC y la predicción de demanda.
    Es todo o nada: si algún rack no existe, no se guarda nada.
    """
    hoy = hoy_local()
    fecha = datos.fecha or hoy
    if fecha > hoy:
        raise HTTPException(status_code=400, detail="La fecha del surtido no puede ser futura.")
    try:
        registrado = registrar_surtido(db, [(i.rack_id, i.unidades) for i in datos.items], fecha)
    except RackNoSurtible:
        raise HTTPException(status_code=400, detail="El punto de salida (DEPOT) no se surte: registra solo racks.")
    except RackNoEncontrado as error:
        raise HTTPException(status_code=404, detail=f"Racks no encontrados: {', '.join(error.args[0])}.")

    return RespuestaSurtidoDTO(
        fecha=fecha,
        racks_actualizados=len(registrado),
        unidades_totales=sum(unidades for _, unidades in registrado),
        detalle=[ItemSurtidoDTO(rack_id=rack_id, unidades=unidades) for rack_id, unidades in registrado],
    )
