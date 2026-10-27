from datetime import date, timedelta

from servicios.demanda import predecir_demanda


def fechas(n):
    return [date(2026, 1, 1) + timedelta(days=i) for i in range(n)]


def test_demanda_creciente_se_detecta_y_se_proyecta():
    resultado = predecir_demanda(fechas(10), [10 + 2 * i for i in range(10)])  # 10, 12, 14 ...

    assert resultado["tendencia"] == "creciente"
    assert resultado["prediccion_diaria"][0] == 30.0  # el día 11 sigue la recta
    assert len(resultado["prediccion_diaria"]) == 7
    assert resultado["prediccion_semana"] == sum(resultado["prediccion_diaria"])


def test_demanda_constante_es_estable_y_no_se_vuelve_negativa():
    estable = predecir_demanda(fechas(10), [5] * 10)
    assert estable["tendencia"] == "estable"
    assert estable["prediccion_semana"] == 35.0

    # una caída fuerte nunca produce pronósticos negativos
    cae = predecir_demanda(fechas(10), [20 - 2 * i for i in range(10)])
    assert cae["tendencia"] == "decreciente"
    assert min(cae["prediccion_diaria"]) >= 0
