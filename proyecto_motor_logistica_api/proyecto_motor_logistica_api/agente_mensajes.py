"""
Asistente de mensajes para el encargado y el empleado del almacén.

Lee los paquetes que la persona registró (con su fecha de entrega) y arma
mensajes de apoyo y consejos según el rol:

- empleado: acciones concretas e inmediatas (qué sacar primero, qué ruta armar).
- encargado: vista de supervisión (vencidos, carga por rack, reubicaciones).

Igual que en agente_espacio.py, el texto pasa por `generar_texto_con_ia`:
hoy devuelve el mensaje armado con plantillas (sin costo); al conectar Azure
OpenAI, esa misma función puede reescribirlo con un tono más natural.
Nota: cuando se conecte un modelo real, conviene unir todos los mensajes en
una sola llamada (o guardarlos en caché), para no hacer una llamada por mensaje
cada vez que se refresca el panel.
"""

import logging
import os
from collections import Counter
from datetime import date, datetime
from typing import Dict, List, Optional
from zoneinfo import ZoneInfo

from sqlalchemy.orm import Session

from models import Paquete
from agente_espacio import generar_texto_con_ia, generar_recomendaciones

logger = logging.getLogger(__name__)

# El contenedor trabaja en UTC; sin esto, por la tarde-noche en México el
# "hoy" del servidor ya sería mañana y los paquetes de hoy saldrían vencidos.
try:
    ZONA_HORARIA: Optional[ZoneInfo] = ZoneInfo(os.getenv("APP_TIMEZONE", "America/Mexico_City"))
except Exception:
    ZONA_HORARIA = None


def hoy_local() -> date:
    return datetime.now(ZONA_HORARIA).date() if ZONA_HORARIA else date.today()


def paquete_a_dict(p: Paquete, hoy: Optional[date] = None) -> Dict:
    hoy = hoy or hoy_local()
    return {
        "id": p.id,
        "codigo": p.codigo,
        "descripcion": p.descripcion,
        "rack_id": p.rack_id,
        "fecha_entrega": p.fecha_entrega,
        "dias_restantes": (p.fecha_entrega - hoy).days,
    }


# ---------------------------------------------------------------------------
# Utilidades de redacción
# ---------------------------------------------------------------------------

def _n_paquetes(n: int) -> str:
    return f"{n} paquete" + ("" if n == 1 else "s")


def _plazo(dias: int) -> str:
    if dias < 0:
        return f"venció hace {abs(dias)} día" + ("" if abs(dias) == 1 else "s")
    if dias == 0:
        return "hoy"
    if dias == 1:
        return "mañana"
    return f"en {dias} días"


def _s(n: int) -> str:
    """Terminación para concordar con 1 paquete o varios (lo / los)."""
    return "" if n == 1 else "s"


def _lista(paquetes: List[Paquete], maximo: int = 3) -> str:
    texto = ", ".join(f"{p.codigo} ({p.rack_id})" for p in paquetes[:maximo])
    extra = len(paquetes) - maximo
    return texto + (f" y {extra} más" if extra > 0 else "")


def _racks(paquetes: List[Paquete]) -> str:
    return ", ".join(sorted({p.rack_id for p in paquetes}))


# ---------------------------------------------------------------------------
# Generación de mensajes
# ---------------------------------------------------------------------------

def generar_mensajes(db: Session, rol: str) -> Dict:
    hoy = hoy_local()
    paquetes = db.query(Paquete).order_by(Paquete.fecha_entrega, Paquete.id).all()

    if not paquetes:
        return {
            "rol": rol,
            "resumen": "Todavía no hay paquetes registrados. Abre un rack con el botón «i» y agrega el primero.",
            "paquete_mas_proximo": None,
            "mensajes": [],
        }

    def dias(p: Paquete) -> int:
        return (p.fecha_entrega - hoy).days

    vencidos = [p for p in paquetes if dias(p) < 0]
    de_hoy = [p for p in paquetes if dias(p) == 0]
    proximos_48h = [p for p in paquetes if 1 <= dias(p) <= 2]
    cercanos = de_hoy + proximos_48h  # hoy, mañana y pasado mañana

    # El más próximo a entregarse: el de fecha más cercana que aún no vence.
    # Si todos están vencidos, se muestra el más atrasado.
    futuros = [p for p in paquetes if dias(p) >= 0]
    mas_proximo = futuros[0] if futuros else paquetes[0]

    n_racks = len({p.rack_id for p in paquetes})
    resumen = (
        f"Hay {_n_paquetes(len(paquetes))} en {n_racks} rack{'' if n_racks == 1 else 's'}. "
        f"Próxima entrega: {mas_proximo.codigo} ({mas_proximo.rack_id}), {_plazo(dias(mas_proximo))}."
    )

    mensajes = []  # lista de (tipo, texto); tipo: urgente | aviso | consejo | info

    if rol == "encargado":
        if vencidos:
            pct = round(len(vencidos) / len(paquetes) * 100)
            mensajes.append((
                "urgente",
                f"Hay {_n_paquetes(len(vencidos))} con la entrega vencida ({pct}% del total): "
                f"{_lista(vencidos)}. Revisa con el equipo qué pasó y reasigna prioridades.",
            ))
        if cercanos:
            mensajes.append((
                "aviso",
                f"{_n_paquetes(len(cercanos))} con entrega hoy o en las próximas 48 horas, "
                f"en {_racks(cercanos)}. Asigna personal a esos racks para no retrasar los envíos.",
            ))

        conteo = Counter(p.rack_id for p in paquetes)
        rack_top, n_top = conteo.most_common(1)[0]
        pct_top = round(n_top / len(paquetes) * 100)
        if len(paquetes) >= 5 and pct_top >= 40:
            mensajes.append((
                "consejo",
                f"El rack {rack_top} concentra {n_top} de {len(paquetes)} paquetes ({pct_top}%). "
                f"Considera repartirlos en otros racks para evitar cuellos de botella al surtir.",
            ))

        # Sugerencia de reubicación del agente de espacio (si hay historial).
        try:
            sugerencias = generar_recomendaciones(db)["recomendaciones"]
            if sugerencias:
                mejor = max(sugerencias, key=lambda r: r["ahorro_distancia"])
                mensajes.append((
                    "consejo",
                    f"Para reducir recorridos, mueve el producto de {mejor['rack_actual']} "
                    f"(alta rotación) a {mejor['rack_sugerido']}, que está vacío y más cerca de la salida: "
                    f"ahorraría {mejor['ahorro_distancia']} unidades de distancia por viaje.",
                ))
        except Exception:
            logger.warning("No se pudo obtener la sugerencia de reubicación.", exc_info=True)

        if not mensajes:
            mensajes.append(("info", "Operación al día: no hay entregas vencidas ni inmediatas."))

    else:  # empleado
        if vencidos:
            mensajes.append((
                "urgente",
                f"Tienes {_n_paquetes(len(vencidos))} con la entrega vencida: {_lista(vencidos)}. "
                f"Sácalo{_s(len(vencidos))} primero y avisa al encargado.",
            ))
        if de_hoy:
            mensajes.append((
                "urgente",
                f"Hoy hay que entregar {_n_paquetes(len(de_hoy))}: {_lista(de_hoy)}. "
                f"Prepáralo{_s(len(de_hoy))} antes de seguir con el resto.",
            ))
        if proximos_48h:
            n48 = len(proximos_48h)
            accion = (
                "Selecciónalo en el mapa y calcula la ruta óptima."
                if n48 == 1
                else "Selecciónalos en el mapa y calcula la ruta óptima para recogerlos en un solo recorrido."
            )
            mensajes.append((
                "aviso",
                f"En las próximas 48 horas {'sale' if n48 == 1 else 'salen'} {_n_paquetes(n48)} "
                f"desde {_racks(proximos_48h)}. {accion}",
            ))
        if not mensajes:
            mensajes.append((
                "info",
                "Vas al día: no hay entregas vencidas ni para hoy. "
                "Aprovecha para verificar que los códigos coincidan con las etiquetas.",
            ))

    return {
        "rol": rol,
        "resumen": resumen,
        "paquete_mas_proximo": paquete_a_dict(mas_proximo, hoy),
        "mensajes": [{"tipo": tipo, "texto": generar_texto_con_ia(texto)} for tipo, texto in mensajes],
    }
