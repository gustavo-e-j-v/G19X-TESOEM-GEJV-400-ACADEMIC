import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import SessionLocal
from models import UbicacionRack

def poblar_datos():
    db = SessionLocal()

    # x = posición dentro del pasillo (columna), y = número de pasillo (fila)
    racks_prueba = [
        {"id": "DEPOT", "x": 0, "y": 0, "nombre_producto": "Punto de salida / Depósito", "ocupado": False},

        # Pasillo A (y=1)
        {"id": "RACK_A1", "x": 1, "y": 1, "nombre_producto": "Tornillería", "ocupado": True},
        {"id": "RACK_A2", "x": 2, "y": 1, "nombre_producto": None, "ocupado": False},
        {"id": "RACK_A3", "x": 3, "y": 1, "nombre_producto": None, "ocupado": False},
        {"id": "RACK_A4", "x": 4, "y": 1, "nombre_producto": "Empaques", "ocupado": True},
        {"id": "RACK_A5", "x": 5, "y": 1, "nombre_producto": "Etiquetas", "ocupado": True},

        # Pasillo B (y=2)
        {"id": "RACK_B1", "x": 1, "y": 2, "nombre_producto": None, "ocupado": False},
        {"id": "RACK_B2", "x": 2, "y": 2, "nombre_producto": None, "ocupado": False},
        {"id": "RACK_B3", "x": 3, "y": 2, "nombre_producto": None, "ocupado": False},
        {"id": "RACK_B4", "x": 4, "y": 2, "nombre_producto": None, "ocupado": False},
        {"id": "RACK_B5", "x": 5, "y": 2, "nombre_producto": "Cables", "ocupado": True},

        # Pasillo C (y=3)
        {"id": "RACK_C1", "x": 1, "y": 3, "nombre_producto": None, "ocupado": False},
        {"id": "RACK_C2", "x": 2, "y": 3, "nombre_producto": None, "ocupado": False},
        {"id": "RACK_C3", "x": 3, "y": 3, "nombre_producto": None, "ocupado": False},
        {"id": "RACK_C4", "x": 4, "y": 3, "nombre_producto": None, "ocupado": False},
        {"id": "RACK_C5", "x": 5, "y": 3, "nombre_producto": "Filtros", "ocupado": True},

        # Pasillo D (y=4)
        {"id": "RACK_D1", "x": 1, "y": 4, "nombre_producto": None, "ocupado": False},
        {"id": "RACK_D2", "x": 2, "y": 4, "nombre_producto": None, "ocupado": False},
        {"id": "RACK_D3", "x": 3, "y": 4, "nombre_producto": None, "ocupado": False},
        {"id": "RACK_D4", "x": 4, "y": 4, "nombre_producto": None, "ocupado": False},
    ]

    try:
        for data in racks_prueba:
            existe = db.query(UbicacionRack).filter(UbicacionRack.id == data["id"]).first()
            if not existe:
                rack = UbicacionRack(**data)
                db.add(rack)

        db.commit()
        print("¡Base de datos poblada con éxito!")
    except Exception as e:
        db.rollback()
        print(f"Error al poblar la base de datos: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    poblar_datos()
