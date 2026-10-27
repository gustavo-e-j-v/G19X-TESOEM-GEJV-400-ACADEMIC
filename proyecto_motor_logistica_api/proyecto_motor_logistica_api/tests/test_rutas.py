from types import SimpleNamespace

import pytest

from servicios.rutas import calcular_distancia_manhattan, resolver_tsp


def punto(x, y):
    return SimpleNamespace(x=x, y=y)


def test_distancia_manhattan_suma_horizontal_y_vertical():
    assert calcular_distancia_manhattan(punto(0, 0), punto(3, 4)) == 7
    assert calcular_distancia_manhattan(punto(5, 2), punto(1, 6)) == 8


def test_ruta_en_linea_recta_ordena_los_racks_por_cercania():
    # El origen es el punto 0; los racks llegan desordenados a propósito
    puntos = [punto(0, 0), punto(3, 0), punto(1, 0), punto(2, 0)]
    orden, distancia = resolver_tsp(puntos)

    assert distancia == 6  # ir hasta x=3 y regresar
    assert orden[0] == 0 and orden[-1] == 0  # sale y regresa al origen
    assert sorted(orden[:-1]) == [0, 1, 2, 3]  # visita todos una sola vez


def test_ruta_de_un_cuadrado_recorre_el_perimetro():
    puntos = [punto(0, 0), punto(2, 2), punto(0, 2), punto(2, 0)]
    orden, distancia = resolver_tsp(puntos)

    assert distancia == 8
    assert orden[0] == 0 and orden[-1] == 0
    assert sorted(orden[:-1]) == [0, 1, 2, 3]


def test_un_solo_destino_es_ida_y_vuelta():
    orden, distancia = resolver_tsp([punto(0, 0), punto(5, 3)])

    assert orden == [0, 1, 0]
    assert distancia == 16


def test_sin_destinos_se_rechaza():
    with pytest.raises(ValueError):
        resolver_tsp([punto(0, 0)])
