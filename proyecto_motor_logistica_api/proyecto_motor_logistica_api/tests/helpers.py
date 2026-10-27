from datetime import date

from models import HistorialPicking, UbicacionRack


def sembrar_racks(db, racks):
    """racks: lista de (id, x, y). Crea las ubicaciones indicadas."""
    for rack_id, x, y in racks:
        db.add(UbicacionRack(id=rack_id, x=x, y=y, ocupado=False))
    db.commit()


def sembrar_historial(db, totales):
    """totales: {rack_id: unidades}. Registra todas las unidades en un solo día."""
    for rack_id, unidades in totales.items():
        db.add(HistorialPicking(rack_id=rack_id, fecha=date(2026, 1, 1), cantidad_recogida=unidades))
    db.commit()
