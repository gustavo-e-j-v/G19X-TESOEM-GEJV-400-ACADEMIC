"""Secciones de la documentación (/docs): cada etiqueta es un contenedor."""

TAG_ALMACEN = "Almacén y rutas"
TAG_PAQUETES = "Paquetes"
TAG_ANALISIS = "Análisis de inventario"
TAG_ASISTENTE = "Asistente"

ETIQUETAS = [
    {"name": TAG_ALMACEN, "description": "Racks del almacén y cálculo de la ruta óptima de picking."},
    {"name": TAG_PAQUETES, "description": "Paquetes de cada rack con su fecha de entrega."},
    {"name": TAG_ANALISIS, "description": "Clasificación ABC por rotación y predicción de demanda."},
    {"name": TAG_ASISTENTE, "description": "Mensajes de apoyo por rol y recomendaciones de reubicación."},
]
