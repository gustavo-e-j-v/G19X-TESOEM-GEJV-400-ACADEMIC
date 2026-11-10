# Prueba de instalación en una carpeta limpia, en modo local, con Docker real.
# Sigue SOLO los pasos del README y guarda la bitácora completa en la carpeta desde la que lo ejecutes.
#
# Antes de ejecutarlo, detén tu propio proyecto si está corriendo (usa los puertos 8000, 5173 y 5432):
#   docker compose down        (en la carpeta del backend)
# Uso, desde la carpeta docs\evidencias de tu copia de trabajo:
#   .\probar_instalacion_docker.ps1
#   .\probar_instalacion_docker.ps1 -Repo "https://github.com/usuario/repositorio.git"

param(
  [string]$Repo = "https://github.com/gustavo-e-j-v/G19X-TESOEM-GEJV-400-ACADEMIC.git",
  [string]$Clave = "clave-de-prueba-local"
)

$inicio = (Get-Location).Path
$fecha = Get-Date -Format "yyyy-MM-dd_HH-mm"
$tmp = Join-Path $env:TEMP "prueba_limpia_$fecha"
New-Item -ItemType Directory -Path $tmp | Out-Null
$bitacora = Join-Path $tmp "bitacora.txt"
$env:COMPOSE_PROJECT_NAME = "prueba_limpia"   # contenedores y volumen aparte de los de tu proyecto
$fallas = @()
Start-Transcript -Path $bitacora | Out-Null

function Paso($titulo) { Write-Host ""; Write-Host "=== $titulo ===" -ForegroundColor Cyan }
function Verificar($ok, $mensaje) {
  if ($ok) { Write-Host "[OK]    $mensaje" -ForegroundColor Green }
  else { Write-Host "[FALLA] $mensaje" -ForegroundColor Red; $script:fallas += $mensaje }
}

Paso "Entorno"
docker --version
docker compose version
node -v
npm -v
git --version

Paso "1. Clonar en una carpeta limpia"
git clone $Repo "$tmp\repo"
$hash = (git -C "$tmp\repo" rev-parse --short HEAD)
$etiqueta = (git -C "$tmp\repo" describe --tags --always)
Write-Host "Commit probado: $hash ($etiqueta)" -ForegroundColor Cyan
$back = "$tmp\repo\proyecto_motor_logistica_api\proyecto_motor_logistica_api"
$front = "$tmp\repo\proyecto_motor_logistica_api\frontend"
Verificar (Test-Path "$back\docker-compose.yml") "El repositorio trae el docker-compose.yml"

Paso "2. Backend: .env y docker compose up"
Set-Location $back
Copy-Item .env.example .env
(Get-Content .env) -replace '^POSTGRES_PASSWORD=.*', "POSTGRES_PASSWORD=$Clave" -replace '^AUTH_DISABLED=.*', 'AUTH_DISABLED=true' | Set-Content .env
docker compose up -d --build
Verificar ($LASTEXITCODE -eq 0) "docker compose up -d --build"
$listo = $false
for ($i = 0; $i -lt 45 -and -not $listo; $i++) {
  try { $r = Invoke-WebRequest -Uri "http://localhost:8000/openapi.json" -UseBasicParsing -TimeoutSec 2; $listo = ($r.StatusCode -eq 200) }
  catch { Start-Sleep -Seconds 2 }
}
Verificar $listo "La API responde en http://localhost:8000"
docker compose ps

Paso "3. Seeds dentro del contenedor"
docker compose exec -T api python seed.py
Verificar ($LASTEXITCODE -eq 0) "python seed.py"
docker compose exec -T api python seed_historial.py
Verificar ($LASTEXITCODE -eq 0) "python seed_historial.py"

Paso "4. Comprobar endpoints"
try { $u = Invoke-RestMethod "http://localhost:8000/api/v1/ubicaciones"; Verificar ($u.Count -eq 20) "ubicaciones: $($u.Count) (esperadas 20)" }
catch { Verificar $false "ubicaciones: $_" }
try { $a = Invoke-RestMethod "http://localhost:8000/api/v1/analisis-abc"; Verificar ($a.Count -eq 18) "analisis-abc: $($a.Count) racks (esperados 18)" }
catch { Verificar $false "analisis-abc: $_" }
try { $d = Invoke-WebRequest "http://localhost:8000/docs" -UseBasicParsing; Verificar ($d.StatusCode -eq 200) "/docs responde" }
catch { Verificar $false "/docs: $_" }

Paso "5. Pruebas (forma Docker del README)"
docker compose run --rm --no-deps -e AUTH_DISABLED=true -e DATABASE_URL=sqlite:// api sh -c "pip install -q pytest httpx && python -m pytest"
Verificar ($LASTEXITCODE -eq 0) "pytest dentro de Docker"

Paso "6. Frontend: .env, npm install y compilación"
Set-Location $front
Copy-Item .env.example .env
(Get-Content .env) -replace '^VITE_AUTH_DISABLED=.*', 'VITE_AUTH_DISABLED=true' | Set-Content .env
npm install
Verificar ($LASTEXITCODE -eq 0) "npm install"
npm run build
Verificar ($LASTEXITCODE -eq 0) "npm run build"

Paso "7. Limpiar (borra los contenedores y el volumen de esta prueba)"
Set-Location $back
docker compose down -v

Paso "Resumen"
if ($fallas.Count -eq 0) { Write-Host "Todo OK" -ForegroundColor Green }
else { Write-Host "Fallaron $($fallas.Count) comprobaciones:" -ForegroundColor Red; $fallas | ForEach-Object { Write-Host " - $_" } }
Write-Host ""
Write-Host "Fila para la bitácora (pégala en la tabla 'Commit probado en cada prueba'):"
$resultado = if ($fallas.Count -eq 0) { "Todo OK" } else { "$($fallas.Count) fallas" }
Write-Host "| Docker real (Windows y Docker Desktop) | $(Get-Date -Format 'yyyy-MM-dd') | $hash ($etiqueta) | $resultado | instalacion_docker_$fecha.txt |"
Stop-Transcript | Out-Null

$destino = Join-Path $inicio "instalacion_docker_$fecha.txt"
Copy-Item $bitacora $destino
Set-Location $inicio
Write-Host "Bitácora guardada en: $destino" -ForegroundColor Cyan
