# Motor de Optimización Logística de Almacenes

Aplicación web que calcula la ruta óptima de picking en un almacén, registra los paquetes de cada rack con su fecha de entrega y analiza la rotación del inventario (clasificación ABC, predicción de demanda y recomendaciones de reubicación). Se desarrolló como proyecto de residencia profesional e incluye un asistente que da consejos distintos al encargado y al empleado.

Todo el código y la documentación están en la carpeta [`proyecto_motor_logistica_api`](proyecto_motor_logistica_api/); empieza por su [README](proyecto_motor_logistica_api/README.md).

## Inicio rápido (modo local, sin cuenta de Azure)

Necesitas Docker Desktop y Node.js. Los comandos son de PowerShell y se ejecutan desde la raíz de este repositorio.

**Backend**

```powershell
cd proyecto_motor_logistica_api\proyecto_motor_logistica_api
Copy-Item .env.example .env
(Get-Content .env) -replace '^POSTGRES_PASSWORD=.*', 'POSTGRES_PASSWORD=mi-clave-local' -replace '^AUTH_DISABLED=.*', 'AUTH_DISABLED=true' | Set-Content .env
docker compose up -d --build
docker compose exec api python seed.py
docker compose exec api python seed_historial.py
```

**Frontend** (en otra terminal, también desde la raíz de este repositorio)

```powershell
cd proyecto_motor_logistica_api\frontend
Copy-Item .env.example .env
(Get-Content .env) -replace '^VITE_AUTH_DISABLED=.*', 'VITE_AUTH_DISABLED=true' | Set-Content .env
npm install
npm run dev
```

Abre `http://localhost:5173` (aplicación) y `http://localhost:8000/docs` (documentación de la API).

## Enlaces

- [README del proyecto](proyecto_motor_logistica_api/README.md): configuración, Microsoft Entra ID, pruebas y limitaciones conocidas.
- [Historial de versiones](proyecto_motor_logistica_api/CHANGELOG.md)
- [PRD y MVP](proyecto_motor_logistica_api/docs/PRD_MVP.md)
- [Evidencias de la instalación en carpeta limpia](proyecto_motor_logistica_api/docs/evidencias/)

Este proyecto se desarrolló con apoyo de asistentes de inteligencia artificial; la declaración completa está en el README del proyecto.

# Historial de Git

| Commit | Etiqueta | Mensaje |
|---|---|---|
| `983390b` | | Merge branch 'main' de GitHub: README de la raiz y PRD |
| `df5917b` | `v0.14-snapshot` | Actualizar CHANGELOG y PRD para las versiones 0.13 y 0.14 |
| `a0c5cbf` | | Agregar el boton Ruta surtida y la ventana de captura |
| `dafae13` | | Agregar el endpoint POST /api/v1/picking/ruta-surtida con sus pruebas |
| `475369d` | `v0.13-snapshot` | Agregar la bitacora y capturas de la instalacion limpia |
| `2d2c7ab` | | Agregar la seccion Inicio rapido (modo local) al README |
| `c37b672` | | Dejar las plantillas .env.example solo con ASCII |
| `08a1fb2` | | Corregir seed.py: crear tablas y terminar con codigo 1 si falla |
| `d57e852` | | Update PRD_MVP.md |
| `825e442` | | Add files via upload |
| `f303a1a` | | Update PRD_MVP.md |
| `b51c94c` | | Update PRD_MVP.md |
| `95841f2` | | Ampliar el README de la raíz con enlaces al proyecto |
| `bfb50cf` | `v0.12-snapshot` | Merge branch 'main' of https://github.com/gustavo-e-j-v/G19X-TESOEM-GEJV-400-ACADEMIC |
| `954f56f` | | Agrega las correcciones faltantes del 3 corte |
| `5934ce9` | | Update README.md |
| `9009c9f` | | Update README.md |
| `6e69e40` | `v0.9-snapshot` | Motor de optimización logística - snapshot 0.9 |
| `4f076cc` | | Initial commit |
