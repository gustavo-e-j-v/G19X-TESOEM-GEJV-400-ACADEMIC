# Motor de Optimización Logística de Almacenes — Notas de la app

Bitácora de versiones del proyecto. **[Snapshot de prueba]** = etapa exploratoria o pendiente de validar en el entorno real; **[Versión]** = funcionalidad completa y probada de punta a punta.

---

#### 0.1 — [Snapshot de prueba] Backend base
Primera prueba del backend corriendo localmente, sin Docker todavía.
- Proyecto creado en Visual Studio (Python + FastAPI).
- Modelo `UbicacionRack` (id, nombre_producto, x, y, activo) sobre PostgreSQL con SQLAlchemy.
- Algoritmo TSP con OR-Tools (distancia Manhattan) para rutas de picking.
- Endpoint `POST /api/v1/optimizar-ruta-bd` funcionando contra una base de datos local.
- Corregidos errores de importación y de ubicación de archivos en el proyecto de Visual Studio.

## 0.2 — [Snapshot de prueba] Dockerización
Primera prueba de que el backend corre igual dentro de un contenedor.
- `Dockerfile`, `docker-compose.yml`, `requirements.txt`, `.dockerignore`.
- PostgreSQL en su propio contenedor, con volumen persistente.
- Resuelto conflicto de puerto 5432 con un PostgreSQL nativo de Windows.
- `seed.py` para poblar datos de prueba.

## 0.3 — [Versión] Datos de almacén por pasillos
- Campo `ocupado` (booleano) agregado al modelo, para representar lleno/vacío.
- Datos de prueba organizados en 4 pasillos.
- Endpoint `GET /api/v1/ubicaciones` para listar todos los racks.
- CORS habilitado para el frontend.

## 0.4 — [Versión] Frontend en React
- Proyecto React con Vite, en carpeta independiente `frontend/`.
- `ShelfGrid`: cuadrícula de estantes por pasillo, color rojo (lleno) / verde (vacío).
- Selección de racks por clic, cálculo de ruta óptima conectado a la API, orden de visita numerado.
- Diseño visual con paleta industrial (ámbar + acero), tipografía IBM Plex Sans/Mono.

## 0.5 — [Versión] Autenticación con Microsoft Entra ID
- Dos apps registradas en Entra ID: `motor-logistica-api` (backend, scope `access_as_user`) y `motor-logistica-frontend` (SPA).
- Backend protegido con `fastapi-azure-auth`.
- Frontend integrado con `@azure/msal-browser` / `@azure/msal-react`: login, token, header `Authorization: Bearer`.
- Corregido: tokens v1.0 vs v2.0 (`requestedAccessTokenVersion: 2` en el manifest).
- Corregido: rechazo de cuentas "guest" (`allow_guest_users=True`).
- Plataforma SPA agregada a `motor-logistica-api` con redirect URI `http://localhost:8000/oauth2-redirect`, para poder autorizar desde `/docs`.

## 0.6 — [Versión] Clasificación ABC y predicción de demanda
- Tabla `historial_picking` (rack_id, fecha, cantidad_recogida).
- `seed_historial.py`: 90 días de historial simulado con patrones de alta/media/baja rotación.
- `GET /api/v1/analisis-abc`: clasifica cada rack en A/B/C según su participación acumulada en el total recogido (pandas).
- `GET /api/v1/prediccion-demanda/{rack_id}`: predice demanda de la próxima semana con regresión lineal (scikit-learn), incluye tendencia.
- Decisión: algoritmo corre en el backend (sin costo) en vez de un workspace de Azure ML.

## 0.7 — [Versión] Agente de recomendaciones de espacio
- `agente_espacio.py`: combina clasificación ABC + ocupación + distancia al punto de salida (DEPOT) para aplicar el principio de slotting (lo que más rota, más cerca del origen).
- Detecta racks de clase A lejanos con un rack vacío más cercano disponible, y arma una recomendación con el ahorro de distancia estimado.
- `GET /api/v1/recomendaciones-espacio`: devuelve un resumen del agente + la lista de recomendaciones con explicación en lenguaje natural.
- Punto único de integración con Azure OpenAI dejado listo (`generar_texto_con_ia`): hoy usa una plantilla simple, mañana se reemplaza por una llamada real sin tocar el resto del agente.

## 0.8 — [Snapshot de prueba] Paquetes por rack y asistente por rol
- Tabla `paquetes` (código único, descripción, rack, fecha de entrega) y modelo `Paquete`.
- Endpoints `GET` y `POST /api/v1/racks/{rack_id}/paquetes` y `DELETE /api/v1/paquetes/{paquete_id}`.
- `GET /api/v1/ubicaciones` ahora incluye `num_paquetes` y `fecha_entrega_mas_proxima`.
- Un rack pasa a "lleno" al agregar un paquete y a "vacío" al eliminar el último.
- Frontend: contador de paquetes en cada estante y botón «i» que abre una ventana emergente (`RackModal`) para ver, agregar y eliminar paquetes.
- Asistente por rol (`agente_mensajes.py`, `GET /api/v1/mensajes-agente?rol=`): mensajes y consejos distintos para empleado y encargado (paquetes vencidos, de hoy y de las próximas 48 h) y la entrega más próxima (`AgentPanel`).
- Las fechas se calculan con la hora de México (variable `APP_TIMEZONE`).

## 0.9 — [Snapshot de prueba] Rediseño de la documentación de la API
- `/docs` con tema propio (`docs_tema.py`): paleta grafito con acento turquesa, encabezado y barra de acceso.
- Endpoints organizados en 4 secciones (Almacén y rutas, Paquetes, Análisis de inventario, Asistente), con títulos en español y acomodados como tarjetas en dos columnas; la tarjeta abierta ocupa todo el ancho.
- Se conserva el botón Authorize con Microsoft y la página de retorno `/oauth2-redirect`.
- Versión de la API: 1.3.1.

## 0.10 — [Snapshot de prueba] Seguridad y configuración
- La contraseña de la base de datos sale del código: `database.py` y `docker-compose.yml` la leen de `.env`; se agrega `.env.example` con valores de ejemplo.
- `docker-compose.yml` ya no contiene valores sensibles: exige `POSTGRES_PASSWORD`, publica PostgreSQL solo en `127.0.0.1` y `.dockerignore` excluye el `.env` de la imagen.
- Identificadores de Entra ID, CORS y zona horaria pasan a variables de entorno (`config.py`); `AZURE_ALLOW_GUEST_USERS` queda desactivado por defecto.
- Frontend: identificadores de Entra ID y dirección de la API en variables `VITE_*` (`.env.example`), con una pantalla de aviso si falta configurarlas.
- Modo local sin Entra ID: `AUTH_DISABLED=true` en el backend y `VITE_AUTH_DISABLED=true` en el frontend, solo para desarrollo o revisión.
- README ampliado: configuración, guía para registrar las apps en Entra ID, modo local y declaración del uso de IA.

## 0.11 — [Snapshot de prueba] Refactor del backend y pruebas
- `main.py` dividido en `config.py`, `seguridad.py`, `schemas.py`, `servicios/` (ruta y demanda) y `routers/` (almacén, paquetes, análisis y asistente).
- Eliminada la clasificación ABC duplicada: el endpoint usa `calcular_clasificacion_abc` de `agente_espacio.py`.
- La ruta óptima valida la petición: al menos un destino, sin repetidos y sin el origen como destino.
- La predicción devuelve la serie reciente y el pronóstico diario (para la gráfica) y ya no produce valores negativos.
- 17 pruebas con pytest: ruta óptima (TSP), clasificación ABC, predicción de demanda y API.
- Versión de la API: 1.4.0.

## 0.12 — [Snapshot de prueba] Vista de análisis en la interfaz
- Nueva pestaña **Análisis** (junto a **Almacén**) con la clasificación ABC, la predicción de demanda por rack con su gráfica y las recomendaciones de reubicación (RF-12 a RF-14).
- Etiqueta "Modo local" visible cuando la autenticación está desactivada.

**Sobre el historial de Git.** Las versiones 0.1 a 0.8 se desarrollaron en el equipo del autor antes de crear este repositorio y no existen como commits. El historial de Git empieza en el snapshot 0.9 (commit `6e69e40`). Desde la 0.10, cada avance es uno o varios commits.

---

## Pendiente

### Siguiente — [Planeado] Rediseño del frontend
Aplicar la paleta y el acomodo de la documentación de la API a la página de paquetes y al resto de la interfaz.

### 1.0 — [Planeado] CI/CD con GitHub Actions
Pruebas automáticas (las de pytest) y reconstrucción de la imagen Docker en cada push.

### 1.1 — [Planeado] Dashboards con Power BI
KPIs: distancia promedio de picking, productos más movidos, utilización de espacio.

### 1.2 — [Planeado] Documentación técnica final y plan de soporte
