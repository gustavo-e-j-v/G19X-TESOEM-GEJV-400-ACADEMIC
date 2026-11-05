from datetime import timedelta

import pytest

from agente_mensajes import hoy_local
from models import HistorialPicking
from servicios.picking import RackNoEncontrado, RackNoSurtible, registrar_surtido
from tests.helpers import sembrar_racks

RACKS = [("DEPOT", 0, 0), ("RACK_A1", 1, 1), ("RACK_A2", 2, 1), ("RACK_B1", 1, 2)]
URL = "/api/v1/picking/ruta-surtida"


def totales(db):
    return {f.rack_id: f.cantidad_recogida for f in db.query(HistorialPicking).all()}


def test_las_unidades_del_mismo_dia_se_suman(db):
    sembrar_racks(db, RACKS)
    hoy = hoy_local()
    registrar_surtido(db, [("RACK_A1", 5)], hoy)
    registrar_surtido(db, [("RACK_A1", 3), ("RACK_A2", 2)], hoy)

    assert totales(db) == {"RACK_A1": 8, "RACK_A2": 2}
    assert db.query(HistorialPicking).count() == 2  # una fila por rack y día


def test_un_rack_repetido_en_la_misma_ruta_se_suma(db):
    sembrar_racks(db, RACKS)
    registrar_surtido(db, [("RACK_A1", 4), ("RACK_A1", 6)], hoy_local())
    assert totales(db) == {"RACK_A1": 10}


def test_un_rack_inexistente_no_guarda_nada(db):
    sembrar_racks(db, RACKS)
    with pytest.raises(RackNoEncontrado) as error:
        registrar_surtido(db, [("RACK_A1", 5), ("NO_EXISTE", 1)], hoy_local())
    assert error.value.args[0] == ["NO_EXISTE"]
    assert totales(db) == {}  # todo o nada


def test_el_punto_de_salida_no_se_surte(db):
    sembrar_racks(db, RACKS)
    with pytest.raises(RackNoSurtible):
        registrar_surtido(db, [("DEPOT", 1)], hoy_local())


def test_la_clasificacion_abc_usa_lo_que_se_surtio(client, db):
    sembrar_racks(db, RACKS)
    r = client.post(URL, json={"items": [
        {"rack_id": "RACK_A1", "unidades": 80}, {"rack_id": "RACK_A2", "unidades": 15}, {"rack_id": "RACK_B1", "unidades": 5}]})

    assert r.status_code == 200
    assert r.json()["unidades_totales"] == 100 and r.json()["racks_actualizados"] == 3
    abc = client.get("/api/v1/analisis-abc").json()
    assert [(f["rack_id"], f["total_recogidas"], f["clase"]) for f in abc] == [
        ("RACK_A1", 80, "A"), ("RACK_A2", 15, "B"), ("RACK_B1", 5, "C")]


def test_la_prediccion_usa_lo_que_se_surtio(client, db):
    sembrar_racks(db, RACKS)
    hoy = hoy_local()
    for dias_atras in range(10):
        r = client.post(URL, json={"fecha": str(hoy - timedelta(days=dias_atras)),
                                   "items": [{"rack_id": "RACK_A1", "unidades": 10 + dias_atras}]})
        assert r.status_code == 200

    prediccion = client.get("/api/v1/prediccion-demanda/RACK_A1")
    assert prediccion.status_code == 200 and len(prediccion.json()["serie_reciente"]) == 10


def test_validaciones_de_la_peticion(client, db):
    sembrar_racks(db, RACKS)
    manana = str(hoy_local() + timedelta(days=1))
    assert client.post(URL, json={"items": []}).status_code == 422
    assert client.post(URL, json={"items": [{"rack_id": "RACK_A1", "unidades": 0}]}).status_code == 422
    assert client.post(URL, json={"items": [{"rack_id": "DEPOT", "unidades": 1}]}).status_code == 400
    assert client.post(URL, json={"fecha": manana, "items": [{"rack_id": "RACK_A1", "unidades": 1}]}).status_code == 400
    r = client.post(URL, json={"items": [{"rack_id": "RACK_A1", "unidades": 1}, {"rack_id": "NO_EXISTE", "unidades": 1}]})
    assert r.status_code == 404 and "NO_EXISTE" in r.json()["detail"]
    assert totales(db) == {}  # ninguna petición inválida dejó datos
