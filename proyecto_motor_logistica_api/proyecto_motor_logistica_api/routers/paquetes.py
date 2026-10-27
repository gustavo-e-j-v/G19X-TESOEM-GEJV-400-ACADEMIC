"""Paquetes de cada rack (datos capturados por la persona)."""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, Response, Security
from sqlalchemy import func
from sqlalchemy.orm import Session

from agente_mensajes import paquete_a_dict
from database import get_db
from models import Paquete, UbicacionRack
from routers.etiquetas import TAG_PAQUETES
from schemas import PaqueteCrearDTO, PaqueteDTO
from seguridad import requerir_autenticacion

router = APIRouter(prefix="/api/v1", tags=[TAG_PAQUETES], dependencies=[Security(requerir_autenticacion)])


def _obtener_rack_o_404(db: Session, rack_id: str) -> UbicacionRack:
    rack = db.query(UbicacionRack).filter(UbicacionRack.id == rack_id).first()
    if rack is None:
        raise HTTPException(status_code=404, detail=f"El rack '{rack_id}' no existe.")
    return rack


@router.get("/racks/{rack_id}/paquetes", response_model=List[PaqueteDTO], summary="Listar paquetes de un rack")
def listar_paquetes_rack(rack_id: str, db: Session = Depends(get_db)):
    """Paquetes de un rack, del que se entrega primero al que se entrega al final."""
    _obtener_rack_o_404(db, rack_id)
    paquetes = (
        db.query(Paquete).filter(Paquete.rack_id == rack_id).order_by(Paquete.fecha_entrega, Paquete.id).all()
    )
    return [PaqueteDTO(**paquete_a_dict(p)) for p in paquetes]


@router.post("/racks/{rack_id}/paquetes", response_model=PaqueteDTO, status_code=201, summary="Registrar paquete")
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


@router.delete("/paquetes/{paquete_id}", status_code=204, response_class=Response, summary="Eliminar paquete")
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
