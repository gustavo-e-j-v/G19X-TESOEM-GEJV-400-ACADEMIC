from datetime import timedelta

from agente_mensajes import hoy_local
from models import UbicacionRack
from tests.helpers import sembrar_historial, sembrar_racks

RACKS = [("DEPOT", 0, 0), ("RACK_A1", 1, 1), ("RACK_A2", 2, 1), ("RACK_B1", 1, 2)]


def test_docs_y_esquema_openapi(client):
    pagina = client.get("/docs")
    assert pagina.status_code == 200 and "Motor de Optimización Logística" in pagina.text

    esquema = client.get("/openapi.json").json()
    assert [t["name"] for t in esquema["tags"]] == [
        "Almacén y rutas", "Paquetes", "Análisis de inventario", "Asistente",
    ]
    assert sum(len(metodos) for metodos in esquema["paths"].values()) == 9


def test_ruta_optima_sale_y_regresa_al_origen(client, db):
    sembrar_racks(db, RACKS)
    r = client.post("/api/v1/optimizar-ruta-bd", json={"origen_id": "DEPOT", "racks_ids": ["RACK_A2", "RACK_A1"]})

    assert r.status_code == 200
    cuerpo = r.json()
    ids = [p["id"] for p in cuerpo["secuencia_optima"]]
    assert ids[0] == "DEPOT" and ids[-1] == "DEPOT" and sorted(ids[1:-1]) == ["RACK_A1", "RACK_A2"]
    assert cuerpo["distancia_total_unidades"] == 6


def test_ruta_rechaza_peticiones_sin_destinos_validos(client, db):
    sembrar_racks(db, RACKS)
    assert client.post("/api/v1/optimizar-ruta-bd", json={"origen_id": "DEPOT", "racks_ids": []}).status_code == 422
    assert client.post("/api/v1/optimizar-ruta-bd", json={"origen_id": "DEPOT", "racks_ids": ["DEPOT"]}).status_code == 400
    assert client.post("/api/v1/optimizar-ruta-bd", json={"origen_id": "DEPOT", "racks_ids": ["NO_EXISTE"]}).status_code == 404


def test_flujo_de_paquetes_y_estado_del_rack(client, db):
    sembrar_racks(db, RACKS)
    entrega = str(hoy_local() + timedelta(days=2))

    creado = client.post("/api/v1/racks/RACK_A1/paquetes", json={"codigo": "PKG-1", "fecha_entrega": entrega})
    assert creado.status_code == 201 and creado.json()["dias_restantes"] == 2
    assert client.post("/api/v1/racks/RACK_A1/paquetes", json={"codigo": "PKG-1", "fecha_entrega": entrega}).status_code == 409
    assert client.post("/api/v1/racks/DEPOT/paquetes", json={"codigo": "X", "fecha_entrega": entrega}).status_code == 400

    rack = next(u for u in client.get("/api/v1/ubicaciones").json() if u["id"] == "RACK_A1")
    assert rack["num_paquetes"] == 1 and rack["ocupado"] is True

    assert client.delete(f"/api/v1/paquetes/{creado.json()['id']}").status_code == 204
    db.expire_all()
    assert db.query(UbicacionRack).filter_by(id="RACK_A1").one().ocupado is False


def test_analisis_abc_y_prediccion(client, db):
    sembrar_racks(db, RACKS)
    assert client.get("/api/v1/analisis-abc").status_code == 404  # todavía no hay historial

    sembrar_historial(db, {"RACK_A1": 80, "RACK_A2": 15, "RACK_B1": 5})
    abc = client.get("/api/v1/analisis-abc")
    assert abc.status_code == 200 and [f["clase"] for f in abc.json()] == ["A", "B", "C"]

    # un solo día de historial no alcanza para predecir
    assert client.get("/api/v1/prediccion-demanda/RACK_A1").status_code == 404


def test_mensajes_del_asistente_por_rol(client, db):
    sembrar_racks(db, RACKS)
    ayer = str(hoy_local() - timedelta(days=1))
    client.post("/api/v1/racks/RACK_A1/paquetes", json={"codigo": "PKG-9", "fecha_entrega": ayer})

    empleado = client.get("/api/v1/mensajes-agente?rol=empleado").json()
    encargado = client.get("/api/v1/mensajes-agente?rol=encargado").json()
    assert empleado["mensajes"][0]["tipo"] == "urgente" and "PKG-9" in empleado["mensajes"][0]["texto"]
    assert encargado["mensajes"][0]["tipo"] == "urgente"
    assert empleado["mensajes"][0]["texto"] != encargado["mensajes"][0]["texto"]
    assert client.get("/api/v1/mensajes-agente?rol=jefe").status_code == 422
