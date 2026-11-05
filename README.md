# Motor de Optimización Logística de Almacenes

Aplicación web que ayuda a operar un almacén con menos recorridos y mejor uso del espacio: calcula la ruta óptima de picking, registra los paquetes de cada rack con su fecha de entrega, analiza la rotación del inventario y da consejos al encargado y al empleado.

Se desarrolló como proyecto de residencia profesional. Estado: **snapshots de prueba 0.8 a 0.12 sobre la versión 0.7 estable** (ver [CHANGELOG](CHANGELOG.md)).

## Funcionalidades

- **Mapa del almacén** por pasillos, con el estado de cada rack (lleno o vacío) y su número de paquetes.
- **Ruta óptima de picking**: se eligen racks con un clic y se calcula el recorrido más corto (problema del agente viajero con OR-Tools y distancia Manhattan).
- **Paquetes por rack**: ventana emergente para ver, agregar y eliminar paquetes con su fecha de entrega.
- **Asistente por rol**: mensajes y consejos distintos para el empleado y el encargado (vencidos, de hoy, próximas 48 h) y la entrega más próxima.
- **Vista de análisis**: clasificación ABC por rotación, predicción de demanda por rack (regresión lineal) y recomendaciones de reubicación.
- **Autenticación** con Microsoft Entra ID (opcional en local, ver más abajo).

## Tecnologías

Python 3.12, FastAPI, SQLAlchemy, PostgreSQL, OR-Tools, pandas, scikit-learn, React, Vite, MSAL, Docker y Docker Compose, pytest.

## Estructura

```
proyecto_motor_logistica_api/
├── README.md, CHANGELOG.md
├── docs/                              PRD, MVP y bitácora
├── proyecto_motor_logistica_api/      BACKEND (FastAPI)
│   ├── main.py                        arma la aplicación
│   ├── config.py, seguridad.py        variables de entorno y autenticación
│   ├── database.py, models.py         conexión y tablas
│   ├── schemas.py                     modelos de entrada y salida
│   ├── routers/                       endpoints: almacén, paquetes, análisis, asistente
│   ├── servicios/                     ruta óptima (TSP) y predicción de demanda
│   ├── agente_espacio.py              clasificación ABC y recomendaciones de reubicación
│   ├── agente_mensajes.py             mensajes del asistente por rol
│   ├── docs_tema.py                   diseño de la página /docs
│   ├── seed.py, seed_historial.py     datos de prueba
│   ├── tests/                         pruebas con pytest
│   ├── .env.example                   plantilla de variables (copiar como .env)
│   └── Dockerfile, docker-compose.yml, requirements*.txt
└── frontend/                          FRONTEND (React + Vite)
    ├── .env.example                   plantilla de variables (copiar como .env)
    └── src/                           App, componentes, api.js, auth.js, authConfig.js
```

## Requisitos

- Docker Desktop
- Node.js 20 o superior (versión LTS)
- Opcional, para correr las pruebas fuera de Docker: Python 3.12

## Configuración

Ninguna contraseña ni identificador está escrito en el código. Todo se lee de archivos `.env`, que **no se suben a Git** (están en `.gitignore`). Cada carpeta trae un `.env.example` con valores de ejemplo, no reales.

**Backend** (`proyecto_motor_logistica_api/proyecto_motor_logistica_api/.env`)

| Variable | Para qué sirve |
|---|---|
| `POSTGRES_PASSWORD` | Contraseña de la base de datos. **Obligatoria**: elige una propia |
| `POSTGRES_USER`, `POSTGRES_DB` | Usuario y nombre de la base (por defecto `postgres` y `almacen_db`) |
| `AZURE_TENANT_ID`, `AZURE_API_CLIENT_ID` | Identificadores de la app del backend en Entra ID |
| `AZURE_ALLOW_GUEST_USERS` | `true` solo si inicias sesión con una cuenta personal o invitada |
| `AUTH_DISABLED` | `true` = modo local sin Entra ID (ver abajo) |
| `CORS_ORIGINS`, `FRONTEND_URL`, `APP_TIMEZONE` | Orígenes permitidos, dirección del frontend y zona horaria de las fechas |

**Frontend** (`proyecto_motor_logistica_api/frontend/.env`)

| Variable | Para qué sirve |
|---|---|
| `VITE_API_BASE` | Dirección de la API (por defecto `http://localhost:8000`) |
| `VITE_AUTH_DISABLED` | `true` = modo local sin Entra ID |
| `VITE_AZURE_TENANT_ID`, `VITE_AZURE_FRONTEND_CLIENT_ID`, `VITE_AZURE_API_CLIENT_ID` | Identificadores de Entra ID |
| `VITE_REDIRECT_URI` | Opcional: URL de retorno del inicio de sesión |

## Cómo levantar el proyecto

1. Abre Docker Desktop y espera a que diga "Engine running".
2. Backend. En la carpeta `proyecto_motor_logistica_api/proyecto_motor_logistica_api`:
   ```powershell
   Copy-Item .env.example .env      # luego edita .env con tus valores
   docker compose up -d --build
   ```
3. Solo la primera vez, carga los datos de prueba dentro del contenedor:
   ```powershell
   docker compose exec api python seed.py
   docker compose exec api python seed_historial.py
   ```
4. Frontend. En la carpeta `proyecto_motor_logistica_api/frontend`:
   ```powershell
   Copy-Item .env.example .env      # luego edita .env con tus valores
   npm install
   npm run dev
   ```
5. Abre la aplicación en `http://localhost:5173` y la documentación de la API en `http://localhost:8000/docs`. Usa `localhost` y no `127.0.0.1`, para que el inicio de sesión de Microsoft funcione.

Si cambias `POSTGRES_PASSWORD` después de haber creado la base, ejecuta `docker compose down -v` (borra los datos de prueba) y vuelve a levantar y sembrar: PostgreSQL solo aplica la contraseña la primera vez que crea el volumen.

## Modo local sin Microsoft Entra ID

Pensado para desarrollo y para que alguien más pueda revisar el proyecto sin registrar aplicaciones en Azure.

1. En el `.env` del backend: `POSTGRES_PASSWORD=<una contraseña>` y `AUTH_DISABLED=true`.
2. En el `.env` del frontend: `VITE_AUTH_DISABLED=true` y `VITE_API_BASE=http://localhost:8000`.
3. Levanta el proyecto como en la sección anterior. La aplicación entra directo, con una etiqueta "Modo local", y `/docs` muestra un aviso de que la autenticación está desactivada.

**No uses `AUTH_DISABLED=true` en un servidor accesible desde internet:** la API no valida ningún token en ese modo.

## Registrar las apps en Microsoft Entra ID

Se necesitan dos registros de aplicación en el [Portal de Azure](https://portal.azure.com) (Microsoft Entra ID, Registros de aplicaciones). Con una cuenta gratuita de Azure es suficiente.

**1. App del backend** (por ejemplo `motor-logistica-api`)

1. Nuevo registro, tipo de cuenta "solo este directorio" (un inquilino), sin URI de redirección.
2. Copia el **Id. de aplicación (cliente)** y el **Id. de directorio (inquilino)**. Van en `AZURE_API_CLIENT_ID` y `AZURE_TENANT_ID`.
3. En *Exponer una API*: acepta el URI de id. de aplicación (`api://<id del cliente>`) y agrega un ámbito llamado `access_as_user` (quién puede dar consentimiento: administradores y usuarios).
4. En *Manifiesto*, dentro de `api`, cambia `requestedAccessTokenVersion` a `2` y guarda.
5. En *Autenticación*, agrega la plataforma **Aplicación de página única (SPA)** con el URI de redirección `http://localhost:8000/oauth2-redirect`. Esto habilita el botón Authorize de `/docs`.

**2. App del frontend** (por ejemplo `motor-logistica-frontend`)

1. Nuevo registro, mismo tipo de cuenta. En URI de redirección elige **SPA** y escribe `http://localhost:5173`.
2. Copia su **Id. de aplicación (cliente)**. Va en `VITE_AZURE_FRONTEND_CLIENT_ID`.
3. En *Permisos de API*: agregar un permiso, API de mi organización, `motor-logistica-api`, permiso delegado `access_as_user`. Después "Conceder consentimiento de administrador".

**3. Llenar los `.env`**: el backend con `AZURE_TENANT_ID` y `AZURE_API_CLIENT_ID`; el frontend con `VITE_AZURE_TENANT_ID`, `VITE_AZURE_FRONTEND_CLIENT_ID` y `VITE_AZURE_API_CLIENT_ID`. Si inicias sesión con una cuenta personal (por ejemplo de Outlook o Gmail) en tu inquilino de pruebas, agrega también `AZURE_ALLOW_GUEST_USERS=true`.

**Acceso para una persona que revisa el proyecto.** Hay dos caminos:

- Usar el **modo local** de la sección anterior (no necesita Azure).
- Pedir acceso a la instancia con Entra ID del autor: el autor invita a la persona en *Entra ID, Usuarios, Invitar usuario externo* con su correo, y la persona inicia sesión con esa cuenta. Para esto el backend debe tener `AZURE_ALLOW_GUEST_USERS=true`.

## Pruebas

Hay 17 pruebas con pytest sobre la ruta óptima (TSP), la clasificación ABC, la predicción de demanda y la API. Usan SQLite en memoria y no necesitan PostgreSQL ni Entra ID.

Con Docker (sin instalar Python), en la carpeta del backend:

```powershell
docker compose run --rm --no-deps -e AUTH_DISABLED=true -e DATABASE_URL=sqlite:// api sh -c "pip install -q pytest httpx && python -m pytest"
```

Con Python local:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
python -m pytest
```

## Seguridad

- No hay contraseñas ni identificadores en el código; se leen de `.env`, ignorado por Git.
- PostgreSQL solo escucha en `127.0.0.1` y la imagen de Docker no incluye el archivo `.env`.
- Todos los endpoints exigen un token válido de Entra ID, salvo en el modo local explícito.
- Una versión de ejemplo de las primeras entregas dejó una contraseña de pruebas en el historial de Git. Era un valor de ejemplo que no se usa en ningún sistema, y desde la versión 0.10 ya no está en el código.

## Historial de versiones

| Versión | Tipo | Resumen |
|---|---|---|
| 0.1 | Snapshot de prueba | Backend base: FastAPI, PostgreSQL y ruta óptima |
| 0.2 | Snapshot de prueba | Dockerización |
| 0.3 | Versión | Datos del almacén por pasillos y estado lleno o vacío |
| 0.4 | Versión | Frontend en React con el mapa de estantes |
| 0.5 | Versión | Autenticación con Microsoft Entra ID |
| 0.6 | Versión | Clasificación ABC y predicción de demanda |
| 0.7 | Versión | Agente de recomendaciones de espacio |
| 0.8 | Snapshot de prueba | Paquetes por rack y asistente por rol |
| 0.9 | Snapshot de prueba | Rediseño de la documentación de la API (`/docs`) |
| 0.10 | Snapshot de prueba | Contraseñas e identificadores fuera del código, modo local |
| 0.11 | Snapshot de prueba | Backend dividido en módulos y pruebas con pytest |
| 0.12 | Snapshot de prueba | Vista de análisis en la interfaz |

El detalle de cada versión está en [CHANGELOG.md](CHANGELOG.md).

**Sobre el historial de Git.** Las versiones 0.1 a 0.8 se desarrollaron en el equipo del autor antes de crear este repositorio y no existen como commits. El historial de Git empieza en el snapshot 0.9 (commit `6e69e40`). Desde la 0.10, cada avance es uno o varios commits con un mensaje descriptivo, y los snapshots se marcan con etiquetas (por ejemplo `v0.9-snapshot`).

## Documentación

- [PRD y MVP](docs/PRD_MVP.md), también en Word: [PRD](docs/PRD_Motor_Logistica_Almacenes.doc) y [MVP](docs/MVP_Motor_Logistica_Almacenes.doc).
- [Bitácora de construcción](docs/bitacora_proyecto.docx) (hasta la versión 0.7).

## Uso de inteligencia artificial

Este proyecto se desarrolló con apoyo de asistentes de inteligencia artificial: Gemini (Google) en la etapa inicial de planeación y Claude (Anthropic) para generar y revisar código, depurar errores, diseñar las pruebas y redactar la documentación. El autor definió el alcance y los requisitos, ejecutó y probó el sistema en su equipo, registró las aplicaciones en Microsoft Entra ID y es responsable del contenido entregado.
