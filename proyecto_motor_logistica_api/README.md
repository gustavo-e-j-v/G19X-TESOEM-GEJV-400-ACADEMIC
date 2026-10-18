# Motor de Optimización Logística de Almacenes

Motor que usa inteligencia artificial y algoritmos de optimización para analizar inventarios, rutas internas, rotación de productos y ocupación de racks, generando recomendaciones para mejorar la distribución física del almacén y reducir recorridos de picking.

## Objetivos específicos
- Analizar procesos logísticos.
- Diseñar la arquitectura tecnológica.
- Implementar algoritmos de optimización.
- Validar desempeño y escalabilidad.
- Elaborar documentación técnica y plan de soporte.

## Stack
Python, FastAPI, PostgreSQL, React.js, Docker, Microsoft Entra ID, OR-Tools, pandas, scikit-learn. Pendiente: Azure OpenAI Service, GitHub Actions, Power BI.

---

## Historial de versiones

Cada entrada está marcada como **[Snapshot de prueba]** (etapa exploratoria, usada para validar que algo funcionaba antes de construir encima) o **[Versión]** (funcionalidad completa y probada de punta a punta).

### 0.1 — [Snapshot de prueba] Backend base
Primera prueba del backend corriendo localmente, sin Docker todavía.
- Proyecto creado en Visual Studio (Python + FastAPI).
- Modelo `UbicacionRack` (id, nombre_producto, x, y, activo) sobre PostgreSQL con SQLAlchemy.
- Algoritmo TSP con OR-Tools (distancia Manhattan) para rutas de picking.
- Endpoint `POST /api/v1/optimizar-ruta-bd` funcionando contra una base de datos local.
- Corregidos errores de importación y de ubicación de archivos en el proyecto de Visual Studio.

### 0.2 — [Snapshot de prueba] Dockerización
Primera prueba de que el backend corre igual dentro de un contenedor.
- `Dockerfile`, `docker-compose.yml`, `requirements.txt`, `.dockerignore`.
- PostgreSQL en su propio contenedor, con volumen persistente.
- Resuelto conflicto de puerto 5432 con un PostgreSQL nativo de Windows.
- `seed.py` para poblar datos de prueba.

### 0.3 — [Versión] Datos de almacén por pasillos
- Campo `ocupado` (booleano) agregado al modelo, para representar lleno/vacío.
- Datos de prueba organizados en 4 pasillos.
- Endpoint `GET /api/v1/ubicaciones` para listar todos los racks.
- CORS habilitado para el frontend.

### 0.4 — [Versión] Frontend en React
- Proyecto React con Vite, en carpeta independiente `frontend/`.
- `ShelfGrid`: cuadrícula de estantes por pasillo, color rojo (lleno) / verde (vacío).
- Selección de racks por clic, cálculo de ruta óptima conectado a la API, orden de visita numerado.
- Diseño visual con paleta industrial (ámbar + acero), tipografía IBM Plex Sans/Mono.

### 0.5 — [Versión] Autenticación con Microsoft Entra ID
- Dos apps registradas en Entra ID: `motor-logistica-api` (backend, scope `access_as_user`) y `motor-logistica-frontend` (SPA).
- Backend protegido con `fastapi-azure-auth`.
- Frontend integrado con `@azure/msal-browser` / `@azure/msal-react`: login, token, header `Authorization: Bearer`.
- Corregido: tokens v1.0 vs v2.0 (`requestedAccessTokenVersion: 2` en el manifest).
- Corregido: rechazo de cuentas "guest" (`allow_guest_users=True`).
- Plataforma SPA agregada a `motor-logistica-api` con redirect URI `http://localhost:8000/oauth2-redirect`, para poder autorizar desde `/docs`.

### 0.6 — [Versión] Clasificación ABC y predicción de demanda
- Tabla `historial_picking` (rack_id, fecha, cantidad_recogida).
- `seed_historial.py`: 90 días de historial simulado con patrones de alta/media/baja rotación.
- `GET /api/v1/analisis-abc`: clasifica cada rack en A/B/C según su participación acumulada en el total recogido (pandas).
- `GET /api/v1/prediccion-demanda/{rack_id}`: predice demanda de la próxima semana con regresión lineal (scikit-learn), incluye tendencia.
- Decisión: algoritmo corre en el backend (sin costo) en vez de un workspace de Azure ML.

### 0.7 — [Versión] Agente de recomendaciones de espacio
- `agente_espacio.py`: combina clasificación ABC + ocupación + distancia al punto de salida (DEPOT) para aplicar el principio de slotting (lo que más rota, más cerca del origen).
- Detecta racks de clase A lejanos con un rack vacío más cercano disponible, y arma una recomendación con el ahorro de distancia estimado.
- `GET /api/v1/recomendaciones-espacio`: devuelve un resumen del agente + la lista de recomendaciones con explicación en lenguaje natural.
- Punto único de integración con Azure OpenAI dejado listo (`generar_texto_con_ia`): hoy usa una plantilla simple, mañana se reemplaza por una llamada real sin tocar el resto del agente.

### 0.8 — [Snapshot de prueba] Paquetes por rack y asistente por rol
- Tabla `paquetes` (código único, descripción, rack, fecha de entrega) y modelo `Paquete`.
- Endpoints `GET` y `POST /api/v1/racks/{rack_id}/paquetes` y `DELETE /api/v1/paquetes/{paquete_id}`.
- `GET /api/v1/ubicaciones` ahora incluye `num_paquetes` y `fecha_entrega_mas_proxima`.
- Un rack pasa a "lleno" al agregar un paquete y a "vacío" al eliminar el último.
- Frontend: contador de paquetes en cada estante y botón «i» que abre una ventana emergente (`RackModal`) para ver, agregar y eliminar paquetes.
- Asistente por rol (`agente_mensajes.py`, `GET /api/v1/mensajes-agente?rol=`): mensajes y consejos distintos para empleado y encargado (paquetes vencidos, de hoy y de las próximas 48 h) y la entrega más próxima (`AgentPanel`).
- Las fechas se calculan con la hora de México (variable `APP_TIMEZONE`).

### 0.9 — [Snapshot de prueba] Rediseño de la documentación de la API
- `/docs` con tema propio (`docs_tema.py`): paleta grafito con acento turquesa, encabezado y barra de acceso.
- Endpoints organizados en 4 secciones (Almacén y rutas, Paquetes, Análisis de inventario, Asistente), con títulos en español y acomodados como tarjetas en dos columnas; la tarjeta abierta ocupa todo el ancho.
- Se conserva el botón Authorize con Microsoft y la página de retorno `/oauth2-redirect`.
- Versión de la API: 1.3.1.

---

## Pendiente

### Siguiente — [Planeado] Rediseño del frontend
Aplicar la paleta y el acomodo de la documentación de la API a la página de paquetes y al resto de la interfaz.

### 1.0 — [Planeado] CI/CD con GitHub Actions
Pruebas automáticas y reconstrucción de la imagen Docker en cada push.

### 1.1 — [Planeado] Dashboards con Power BI
KPIs: distancia promedio de picking, productos más movidos, utilización de espacio.

### 1.2 — [Planeado] Documentación técnica final y plan de soporte

---

## Estructura del proyecto

```
proyecto_motor_logistica_api/              carpeta de la solución (raíz)
├── .gitignore
├── README.md
├── CHANGELOG.md
├── docs/                                  documentación (PRD, MVP, bitácora)
├── proyecto_motor_logistica_api/          BACKEND (FastAPI + PostgreSQL)
│   ├── main.py                            API y endpoints
│   ├── database.py                        conexión a PostgreSQL
│   ├── models.py                          tablas (racks, historial, paquetes)
│   ├── agente_espacio.py                  agente de recomendaciones de espacio
│   ├── agente_mensajes.py                 asistente por rol (encargado / empleado)
│   ├── docs_tema.py                       diseño de la página /docs
│   ├── seed.py                            datos de prueba de racks
│   ├── seed_historial.py                  historial de picking simulado
│   ├── requirements.txt
│   ├── Dockerfile
│   ├── docker-compose.yml
│   └── .dockerignore
└── frontend/                              FRONTEND (React + Vite)
    ├── package.json
    ├── vite.config.js
    ├── index.html
    └── src/
        ├── main.jsx, App.jsx, App.css, paquetes.css
        ├── api.js, authConfig.js, formato.js
        └── components/
            ├── SelectionPanel.jsx, ShelfGrid.jsx
            ├── RackModal.jsx, AgentPanel.jsx
            └── LoginGate.jsx
```

---

## Cómo levantar el proyecto

1. Verifica que el PostgreSQL nativo de Windows esté detenido (evita conflicto con el puerto 5432).
2. Abre Docker Desktop y espera "Engine running".
3. En la carpeta del backend (`proyecto_motor_logistica_api/proyecto_motor_logistica_api`): `docker compose up -d --build`
4. Solo la primera vez (o tras borrar el volumen), carga los datos de prueba dentro del contenedor:
   `docker compose exec api python seed.py` y luego `docker compose exec api python seed_historial.py`
5. En la carpeta `frontend`: `npm install` (solo la primera vez) y `npm run dev`
6. Abre la aplicación en `http://localhost:5173/` y la documentación de la API en `http://localhost:8000/docs` (usa `localhost`, no `127.0.0.1`, para que el inicio de sesión de Microsoft funcione).
