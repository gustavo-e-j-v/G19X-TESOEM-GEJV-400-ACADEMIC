"""
Agente de optimización de espacio del almacén.

Analiza la clasificación ABC de rotación y la ocupación actual de los racks
para recomendar reubicaciones que reduzcan el recorrido promedio de picking:
el principio de "slotting" clásico de logística dice que los productos de
mayor rotación (clase A) deberían estar lo más cerca posible del punto de
salida, y los de baja rotación (clase C) pueden quedar más lejos.

La función `generar_texto_con_ia` es el único punto que habría que cambiar
para conectar un modelo real de Azure OpenAI: hoy arma el texto con
plantillas (gratis, sin dependencias externas), pero la forma de llamarla
desde el resto del agente no cambiaría.
"""

from typing import List, Dict
import pandas as pd
from sqlalchemy.orm import Session
from sqlalchemy import func

from models import UbicacionRack, HistorialPicking

DEPOT_ID = "DEPOT"


def _distancia_manhattan(x1, y1, x2, y2) -> int:
    return abs(x1 - x2) + abs(y1 - y2)


def calcular_clasificacion_abc(db: Session) -> pd.DataFrame:
    """Misma lógica que el endpoint /api/v1/analisis-abc, reutilizada aquí
    para que el agente no tenga que repetir el cálculo."""
    resultados = (
        db.query(HistorialPicking.rack_id, func.sum(HistorialPicking.cantidad_recogida).label("total"))
        .group_by(HistorialPicking.rack_id)
        .all()
    )
    df = pd.DataFrame(resultados, columns=["rack_id", "total"]).sort_values("total", ascending=False)
    if df.empty:
        return df

    total_general = df["total"].sum()
    df["porcentaje_del_total"] = (df["total"] / total_general * 100).round(2)
    df["porcentaje_acumulado"] = df["porcentaje_del_total"].cumsum().round(2)
    df["clase"] = df["porcentaje_acumulado"].apply(lambda p: "A" if p <= 80 else ("B" if p <= 95 else "C"))
    return df


def generar_texto_con_ia(prompt: str) -> str:
    """
    Punto de integración con Azure OpenAI.

    Para conectar un modelo real, reemplaza el cuerpo de esta función por
    algo como:

        from openai import AzureOpenAI
        client = AzureOpenAI(
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
            api_key=os.getenv("AZURE_OPENAI_API_KEY"),
            api_version="2024-10-21",
        )
        respuesta = client.chat.completions.create(
            model=os.getenv("AZURE_OPENAI_DEPLOYMENT"),  # ej. "gpt-4o-mini"
            messages=[
                {"role": "system", "content": "Eres un asesor de logística de almacenes, breve y claro."},
                {"role": "user", "content": prompt},
            ],
        )
        return respuesta.choices[0].message.content

    El resto del agente (generar_recomendaciones) no necesita cambiar nada
    más: solo llama a esta función con el contexto ya armado.
    """
    # --- Implementación actual: plantillas de texto, sin costo ---
    return prompt


def generar_recomendaciones(db: Session) -> Dict:
    df_abc = calcular_clasificacion_abc(db)
    if df_abc.empty:
        return {
            "resumen_agente": "Todavía no hay historial de picking suficiente para generar recomendaciones.",
            "recomendaciones": [],
        }

    ubicaciones = {u.id: u for u in db.query(UbicacionRack).all()}
    depot = ubicaciones.get(DEPOT_ID)
    if depot is None:
        return {"resumen_agente": "No se encontró el punto de salida (DEPOT) en la base de datos.", "recomendaciones": []}

    # Distancia de cada rack al DEPOT
    distancias = {
        rid: _distancia_manhattan(depot.x, depot.y, u.x, u.y)
        for rid, u in ubicaciones.items()
        if rid != DEPOT_ID
    }

    racks_vacios_ordenados = sorted(
        [rid for rid, u in ubicaciones.items() if rid != DEPOT_ID and not u.ocupado],
        key=lambda rid: distancias[rid],
    )

    racks_clase_a = df_abc[df_abc["clase"] == "A"]["rack_id"].tolist()

    recomendaciones = []
    usados = set()

    for rack_id in racks_clase_a:
        if rack_id not in distancias:
            continue
        distancia_actual = distancias[rack_id]

        # Busca el rack vacío disponible más cercano que mejore la distancia actual
        candidato = next(
            (r for r in racks_vacios_ordenados if r not in usados and distancias[r] < distancia_actual),
            None,
        )
        if candidato is None:
            continue

        usados.add(candidato)
        distancia_nueva = distancias[candidato]
        ahorro = distancia_actual - distancia_nueva

        prompt = (
            f"El rack {rack_id} es de clase A (alta rotación) pero está a {distancia_actual} "
            f"unidades del punto de salida. El rack {candidato} está vacío y más cerca "
            f"({distancia_nueva} unidades). Reubicar el producto ahorraría {ahorro} unidades "
            f"de distancia por cada viaje de picking a ese producto."
        )
        explicacion = generar_texto_con_ia(prompt)

        recomendaciones.append({
            "rack_actual": rack_id,
            "clase": "A",
            "distancia_actual": distancia_actual,
            "rack_sugerido": candidato,
            "distancia_sugerida": distancia_nueva,
            "ahorro_distancia": ahorro,
            "explicacion": explicacion,
        })

    if recomendaciones:
        ahorro_total = sum(r["ahorro_distancia"] for r in recomendaciones)
        resumen = (
            f"El agente encontró {len(recomendaciones)} oportunidad(es) de reubicación. "
            f"Aplicarlas todas ahorraría un total de {ahorro_total} unidades de distancia "
            f"en cada ciclo de picking de esos productos."
        )
    else:
        resumen = "La distribución actual ya está razonablemente optimizada: no se encontraron reubicaciones que reduzcan distancia de forma significativa."

    return {"resumen_agente": resumen, "recomendaciones": recomendaciones}
