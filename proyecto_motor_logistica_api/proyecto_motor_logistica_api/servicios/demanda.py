"""Predicción de demanda con regresión lineal sobre el historial diario."""

from datetime import date
from typing import Dict, List, Sequence

import numpy as np
from sklearn.linear_model import LinearRegression

UMBRAL_PENDIENTE = 0.05  # unidades por día; por debajo se considera "estable"


def predecir_demanda(fechas: Sequence[date], cantidades: Sequence[int], dias: int = 7) -> Dict:
    """Ajusta una recta (unidades vs. día) y proyecta los próximos `dias` días."""
    if len(fechas) != len(cantidades) or len(fechas) < 2:
        raise ValueError("Se necesitan al menos dos días de historial.")

    y = np.array(cantidades, dtype=float)
    x = np.array([(f - fechas[0]).days for f in fechas]).reshape(-1, 1)

    modelo = LinearRegression().fit(x, y)
    ultimo_dia = x[-1][0]
    futuros = np.arange(ultimo_dia + 1, ultimo_dia + 1 + dias).reshape(-1, 1)
    pronostico = np.maximum(modelo.predict(futuros), 0)  # la demanda no puede ser negativa

    pendiente = float(modelo.coef_[0])
    if pendiente > UMBRAL_PENDIENTE:
        tendencia = "creciente"
    elif pendiente < -UMBRAL_PENDIENTE:
        tendencia = "decreciente"
    else:
        tendencia = "estable"

    diaria: List[float] = [round(float(v), 2) for v in pronostico]
    return {
        "promedio_diario": round(float(y.mean()), 2),
        "prediccion_semana": round(float(pronostico.sum()), 2),
        "prediccion_diaria": diaria,
        "tendencia": tendencia,
    }
