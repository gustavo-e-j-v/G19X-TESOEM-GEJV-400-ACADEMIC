"""Registro del picking real: confirma que una ruta se surtió.

Cada confirmación suma unidades al historial de picking (una fila por rack y día).
La clasificación ABC y la predicción de demanda se calculan sobre ese historial,
así que se alimentan con lo que pasa en la operación.
"""

from collections import OrderedDict
from datetime import date
from typing import Dict, Iterable, List, Tuple

from sqlalchemy.orm import Session

from models import HistorialPicking, UbicacionRack

ORIGEN = "DEPOT"


class RackNoEncontrado(Exception):
    """Alguno de los racks no existe. args[0] es la lista de ids que faltan."""


class RackNoSurtible(Exception):
    """Se intentó surtir el punto de salida, que no es un rack."""


def registrar_surtido(db: Session, items: Iterable[Tuple[str, int]], fecha: date) -> List[Tuple[str, int]]:
    """Suma las unidades de cada rack al historial del día `fecha`.

    Es todo o nada: si algún rack no existe, no se guarda nada. Si un rack aparece
    varias veces, sus unidades se suman. Devuelve [(rack_id, unidades)].
    """
    por_rack: Dict[str, int] = OrderedDict()
    for rack_id, unidades in items:
        por_rack[rack_id] = por_rack.get(rack_id, 0) + unidades

    if ORIGEN in por_rack:
        raise RackNoSurtible(ORIGEN)

    existentes = {fila.id for fila in db.query(UbicacionRack.id).filter(UbicacionRack.id.in_(list(por_rack))).all()}
    faltan = [rack_id for rack_id in por_rack if rack_id not in existentes]
    if faltan:
        raise RackNoEncontrado(faltan)

    for rack_id, unidades in por_rack.items():
        fila = (
            db.query(HistorialPicking)
            .filter(HistorialPicking.rack_id == rack_id, HistorialPicking.fecha == fecha)
            .first()
        )
        if fila:
            fila.cantidad_recogida += unidades
        else:
            db.add(HistorialPicking(rack_id=rack_id, fecha=fecha, cantidad_recogida=unidades))
    db.commit()
    return list(por_rack.items())
