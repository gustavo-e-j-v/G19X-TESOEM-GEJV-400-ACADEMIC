from agente_espacio import calcular_clasificacion_abc
from models import HistorialPicking
from tests.helpers import sembrar_historial


def clases(df):
    return dict(zip(df["rack_id"], df["clase"]))


def test_clasificacion_con_cortes_80_95_100(db):
    # Totales 80 / 15 / 5  ->  acumulado 80% / 95% / 100%
    sembrar_historial(db, {"R1": 80, "R2": 15, "R3": 5})
    df = calcular_clasificacion_abc(db)

    assert clases(df) == {"R1": "A", "R2": "B", "R3": "C"}
    assert list(df["porcentaje_acumulado"]) == [80.0, 95.0, 100.0]


def test_se_ordena_de_mayor_a_menor_y_el_acumulado_no_baja(db):
    sembrar_historial(db, {"R1": 5, "R2": 50, "R3": 30, "R4": 15})
    df = calcular_clasificacion_abc(db)

    assert list(df["rack_id"]) == ["R2", "R3", "R4", "R1"]
    acumulado = list(df["porcentaje_acumulado"])
    assert acumulado == sorted(acumulado)
    assert acumulado[-1] == 100.0


def test_diez_racks_iguales_se_reparten_entre_a_b_y_c(db):
    sembrar_historial(db, {f"R{i:02d}": 10 for i in range(10)})
    df = calcular_clasificacion_abc(db)

    conteo = df["clase"].value_counts().to_dict()
    assert conteo == {"A": 8, "B": 1, "C": 1}


def test_sin_historial_devuelve_vacio(db):
    assert db.query(HistorialPicking).count() == 0
    assert calcular_clasificacion_abc(db).empty
