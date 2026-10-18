import sys
import os
import random
from datetime import date, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import SessionLocal
from models import UbicacionRack, HistorialPicking

# Patrón de rotación por rack: (promedio diario, variación). Simula que unos
# productos se piden mucho (alta rotación -> clase A), otros poco (clase C).
PATRONES_ROTACION = {
    "RACK_A1": (18, 4),   # alta rotación
    "RACK_A4": (15, 3),
    "RACK_A5": (14, 3),
    "RACK_B5": (12, 3),
    "RACK_C5": (10, 2),
    "RACK_A2": (6, 2),    # rotación media
    "RACK_A3": (5, 2),
    "RACK_B1": (5, 2),
    "RACK_B2": (4, 1),
    "RACK_B3": (4, 1),
    "RACK_C1": (2, 1),    # baja rotación
    "RACK_C2": (1, 1),
    "RACK_C3": (1, 1),
    "RACK_C4": (1, 1),
    "RACK_D1": (1, 1),
    "RACK_D2": (0, 1),
    "RACK_D3": (0, 1),
    "RACK_D4": (0, 1),
}

DIAS_HISTORIAL = 90


def poblar_historial():
    db = SessionLocal()
    try:
        racks_existentes = {r.id for r in db.query(UbicacionRack.id).all()}
        hoy = date.today()

        registros_creados = 0
        for rack_id, (promedio, variacion) in PATRONES_ROTACION.items():
            if rack_id not in racks_existentes:
                continue  # el rack no existe en esta base (por si seed.py cambió)

            for dias_atras in range(DIAS_HISTORIAL):
                fecha = hoy - timedelta(days=dias_atras)
                cantidad = max(0, round(random.gauss(promedio, variacion)))

                existe = (
                    db.query(HistorialPicking)
                    .filter(HistorialPicking.rack_id == rack_id, HistorialPicking.fecha == fecha)
                    .first()
                )
                if existe:
                    continue

                db.add(HistorialPicking(rack_id=rack_id, fecha=fecha, cantidad_recogida=cantidad))
                registros_creados += 1

        db.commit()
        print(f"¡Historial de picking poblado con éxito! ({registros_creados} registros nuevos)")
    except Exception as e:
        db.rollback()
        print(f"Error al poblar el historial: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    poblar_historial()
