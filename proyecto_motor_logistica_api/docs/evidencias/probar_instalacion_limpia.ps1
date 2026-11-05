# Prueba de instalacion en carpeta limpia, en modo local, siguiendo solo el README.
# Uso (desde la raiz del repositorio):  .\docs\evidencias\probar_instalacion_limpia.ps1
# Requiere Docker Desktop abierto y Node.js 20+. Libera los puertos 5432 y 8000 antes de correrlo.
# Clona el ULTIMO COMMIT (no el directorio de trabajo): lo que no este commiteado no se prueba.
param([string]$Repo = (Get-Location).Path)

# Continue: Windows PowerShell 5.1 trata como error lo que docker escribe en stderr; se valida con $LASTEXITCODE
$ErrorActionPreference = "Continue"
$PSDefaultParameterValues["*:ErrorAction"] = "Stop"   # los cmdlets si deben fallar
$fecha   = Get-Date -Format "yyyyMMdd-HHmm"
$destino = Join-Path $Repo "docs\evidencias"
$log     = Join-Path $destino "bitacora_instalacion_$fecha.txt"
$resumen = Join-Path $destino "bitacora_instalacion_$fecha.md"
$limpia  = Join-Path ([IO.Path]::GetTempPath()) "motor_limpio_$fecha"
$pasos   = New-Object System.Collections.ArrayList
$fallo   = $false

Start-Transcript -Path $log | Out-Null

function Paso([string]$nombre, [scriptblock]$accion) {
    if ($script:fallo) { [void]$pasos.Add([pscustomobject]@{ Paso = $nombre; Resultado = "OMITIDO"; Segundos = 0 }); return }
    Write-Host "`n=== $nombre ===" -ForegroundColor Cyan
    $inicio = Get-Date
    try {
        & $accion
        if ($LASTEXITCODE -ne 0 -and $null -ne $LASTEXITCODE) { throw "codigo de salida $LASTEXITCODE" }
        $res = "OK"
    } catch {
        Write-Host "FALLO: $_" -ForegroundColor Red
        $res = "FALLO: $_"
        $script:fallo = $true
    }
    $global:LASTEXITCODE = 0
    [void]$pasos.Add([pscustomobject]@{ Paso = $nombre; Resultado = $res; Segundos = [int]((Get-Date) - $inicio).TotalSeconds })
}

$be = Join-Path $limpia "proyecto_motor_logistica_api\proyecto_motor_logistica_api"
$fe = Join-Path $limpia "proyecto_motor_logistica_api\frontend"
if (-not (Test-Path (Join-Path $limpia "proyecto_motor_logistica_api"))) { $be = Join-Path $limpia "proyecto_motor_logistica_api"; $fe = Join-Path $limpia "frontend" }

try {
    Paso "Clonar el repositorio en una carpeta limpia ($limpia)" { git clone --quiet $Repo $limpia }
    Paso "Backend: .env en modo local (POSTGRES_PASSWORD y AUTH_DISABLED=true)" {
        Copy-Item (Join-Path $be ".env.example") (Join-Path $be ".env")
        (Get-Content (Join-Path $be ".env")) `
            -replace "^POSTGRES_PASSWORD=.*", "POSTGRES_PASSWORD=clave-de-prueba-local" `
            -replace "^AUTH_DISABLED=.*", "AUTH_DISABLED=true" | Set-Content (Join-Path $be ".env")
    }
    Paso "Backend: docker compose up -d --build" { Push-Location $be; try { docker compose up -d --build } finally { Pop-Location } }
    Paso "Backend: esperar a que la API responda en /docs (maximo 120 s)" {
        $ok = $false
        for ($i = 0; $i -lt 40 -and -not $ok; $i++) {
            try { $ok = (Invoke-WebRequest "http://localhost:8000/docs" -UseBasicParsing -TimeoutSec 3).StatusCode -eq 200 } catch { Start-Sleep 3 }
        }
        if (-not $ok) { throw "la API no respondio" }
    }
    Paso "Backend: seed.py" { Push-Location $be; try { docker compose exec -T api python seed.py } finally { Pop-Location } }
    Paso "Backend: seed_historial.py" { Push-Location $be; try { docker compose exec -T api python seed_historial.py } finally { Pop-Location } }
    Paso "API: GET /api/v1/ubicaciones devuelve racks" {
        $r = Invoke-RestMethod "http://localhost:8000/api/v1/ubicaciones"
        if ($r.Count -lt 2) { throw "pocas ubicaciones: $($r.Count)" }
        Write-Host "Ubicaciones: $($r.Count)"
    }
    Paso "API: POST /api/v1/picking/ruta-surtida guarda y la ABC responde" {
        $rack = (Invoke-RestMethod "http://localhost:8000/api/v1/ubicaciones" | Where-Object { $_.id -ne "DEPOT" } | Select-Object -First 1).id
        $cuerpo = @{ items = @(@{ rack_id = $rack; unidades = 3 }) } | ConvertTo-Json -Depth 4
        Invoke-RestMethod "http://localhost:8000/api/v1/picking/ruta-surtida" -Method Post -Body $cuerpo -ContentType "application/json" | Out-String | Write-Host
        $abc = Invoke-RestMethod "http://localhost:8000/api/v1/analisis-abc"
        Write-Host "Racks en la ABC: $($abc.Count)"
    }
    Paso "API: ?rol= funciona en modo local" {
        $r = Invoke-RestMethod "http://localhost:8000/api/v1/mensajes-agente?rol=encargado"
        if ($r.rol -ne "encargado") { throw "rol inesperado: $($r.rol)" }
    }
    Paso "Pruebas (comando del README, con Docker)" {
        Push-Location $be
        try { docker compose run --rm --no-deps -e AUTH_DISABLED=true -e DATABASE_URL=sqlite:// api sh -c "pip install -q pytest httpx && python -m pytest" }
        finally { Pop-Location }
    }
    Paso "Frontend: .env en modo local" {
        Copy-Item (Join-Path $fe ".env.example") (Join-Path $fe ".env")
        (Get-Content (Join-Path $fe ".env")) `
            -replace "^VITE_AUTH_DISABLED=.*", "VITE_AUTH_DISABLED=true" `
            -replace "^VITE_API_BASE=.*", "VITE_API_BASE=http://localhost:8000" | Set-Content (Join-Path $fe ".env")
        if (-not (Select-String -Path (Join-Path $fe ".env") -Pattern "^VITE_AUTH_DISABLED=true")) { Add-Content (Join-Path $fe ".env") "VITE_AUTH_DISABLED=true" }
    }
    Paso "Frontend: npm install" { Push-Location $fe; try { npm install } finally { Pop-Location } }
    Paso "Frontend: npm run build (compila; el README usa npm run dev, que no termina)" { Push-Location $fe; try { npm run build } finally { Pop-Location } }
}
finally {
    Write-Host "`n=== Limpieza: docker compose down -v ===" -ForegroundColor Cyan
    if (Test-Path $be) { Push-Location $be; try { docker compose down -v } catch { Write-Host "No se pudo limpiar: $_" } finally { Pop-Location } }

    $lineas = @("# Bitacora de instalacion en carpeta limpia", "",
        "- Fecha: $(Get-Date -Format 'yyyy-MM-dd HH:mm')", "- Commit probado: $(git -C $Repo rev-parse --short HEAD)",
        "- Modo: local (AUTH_DISABLED=true)", "- Registro completo: $(Split-Path $log -Leaf)", "",
        "| Paso | Resultado | Segundos |", "|---|---|---|")
    $lineas += $pasos | ForEach-Object { "| $($_.Paso) | $($_.Resultado) | $($_.Segundos) |" }
    $lineas += @("", "## Fallos encontrados y correcciones", "", "(Anota aqui que fallo, la causa y el commit que lo corrige.)")
    $lineas | Set-Content -Path $resumen -Encoding UTF8
    Stop-Transcript | Out-Null
    Write-Host "`nBitacora: $resumen" -ForegroundColor Green
}
