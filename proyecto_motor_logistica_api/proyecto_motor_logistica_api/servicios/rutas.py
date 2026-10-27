"""Cálculo de la ruta óptima de picking (problema del agente viajero, TSP).

No depende de FastAPI ni de la base de datos: recibe puntos con coordenadas
`x` e `y`, de modo que se puede probar de forma aislada.
"""

from typing import List, Protocol, Sequence, Tuple

from ortools.constraint_solver import pywrapcp, routing_enums_pb2


class Punto(Protocol):
    x: int
    y: int


def calcular_distancia_manhattan(p1: Punto, p2: Punto) -> int:
    return abs(p1.x - p2.x) + abs(p1.y - p2.y)


def resolver_tsp(puntos: Sequence[Punto]) -> Tuple[List[int], int]:
    """Devuelve (orden de visita, distancia total).

    El punto 0 es el origen: la ruta sale de ahí y regresa a él. El orden son
    índices de `puntos`, por ejemplo [0, 2, 1, 3, 0].
    """
    if len(puntos) < 2:
        raise ValueError("Se necesitan al menos dos puntos: el origen y un destino.")

    n = len(puntos)
    matriz = [[calcular_distancia_manhattan(puntos[i], puntos[j]) for j in range(n)] for i in range(n)]

    manager = pywrapcp.RoutingIndexManager(n, 1, 0)
    routing = pywrapcp.RoutingModel(manager)

    def distancia(desde: int, hasta: int) -> int:
        return matriz[manager.IndexToNode(desde)][manager.IndexToNode(hasta)]

    indice_costo = routing.RegisterTransitCallback(distancia)
    routing.SetArcCostEvaluatorOfAllVehicles(indice_costo)

    parametros = pywrapcp.DefaultRoutingSearchParameters()
    parametros.first_solution_strategy = routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC

    solucion = routing.SolveWithParameters(parametros)
    if not solucion:
        raise ValueError("No se pudo calcular una ruta de picking.")

    indice = routing.Start(0)
    orden: List[int] = []
    total = 0
    while not routing.IsEnd(indice):
        orden.append(manager.IndexToNode(indice))
        anterior = indice
        indice = solucion.Value(routing.NextVar(indice))
        total += routing.GetArcCostForVehicle(anterior, indice, 0)
    orden.append(manager.IndexToNode(indice))
    return orden, total
