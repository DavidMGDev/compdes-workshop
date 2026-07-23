# =============================================================================
#  setup.ps1 — Instalador guiado del taller (Windows PowerShell)
# =============================================================================
#  Equivalente exacto de setup.sh, para Windows. Puede hacerlo A MANO
#  siguiendo docs/SETUP.md.
#
#  USO (desde la carpeta del repo):
#      powershell -ExecutionPolicy Bypass -File install\setup.ps1
#
#  El flag -ExecutionPolicy Bypass evita el bloqueo de scripts de Windows
#  solo para esta ejecución; no cambia la configuración del sistema.
# =============================================================================
$ErrorActionPreference = "Stop"   # aborta ante el primer error

# Nos ubicamos en la raíz del repo (un nivel arriba de \install).
$Raiz = Split-Path -Parent $PSScriptRoot
Set-Location $Raiz
Write-Host "==> Raiz del taller: $Raiz"

# --- Paso 1: prerrequisitos ------------------------------------------------
Write-Host "`n==> [1/5] Comprobando prerrequisitos..."
$falta = $false
$py = Get-Command python -ErrorAction SilentlyContinue
if ($py) { Write-Host "    OK $(python --version)" }
else { Write-Host "    FALTA python (obligatorio)"; $falta = $true }
$dk = Get-Command docker -ErrorAction SilentlyContinue
if ($dk) { Write-Host "    OK $(docker --version)" }
else { Write-Host "    FALTA docker (obligatorio para el laboratorio)"; $falta = $true }
if ($falta) { Write-Host "    Instale lo que falta y reintente."; exit 1 }

# --- Paso 2: entorno virtual ----------------------------------------------
Write-Host "`n==> [2/5] Creando entorno virtual (.venv)..."
if (Test-Path .venv) {
  Write-Host "    .venv ya existe, lo reutilizo."
} else {
  python -m venv .venv
  Write-Host "    OK creado"
}
# En Windows el ejecutable del venv está en .venv\Scripts\python.exe.
# Lo llamamos directamente en vez de 'activar', para no depender de la
# política de ejecución del Activate.ps1.
$vpy = Join-Path $Raiz ".venv\Scripts\python.exe"

# --- Paso 3: dependencias --------------------------------------------------
Write-Host "`n==> [3/5] Instalando dependencias (puede tardar varios minutos)..."
& $vpy -m pip install --upgrade pip | Out-Null
& $vpy -m pip install -r requirements.txt
Write-Host "    OK dependencias instaladas"

# --- Paso 4: archivo .env --------------------------------------------------
Write-Host "`n==> [4/5] Configurando .env..."
if (Test-Path .env) {
  Write-Host "    .env ya existe, no lo toco."
} else {
  Copy-Item .env.example .env
  Write-Host "    OK .env creado a partir de la plantilla."
  Write-Host "    >>> AHORA edite .env y pegue su llave en OPENAI_API_KEY <<<"
}

# --- Paso 5: diagnóstico ---------------------------------------------------
Write-Host "`n==> [5/5] Diagnostico del entorno..."
try { & $vpy install\check_setup.py } catch { }   # informa, no aborta

Write-Host "`n============================================================"
Write-Host "Instalacion terminada."
Write-Host "Siguientes pasos:"
Write-Host "  1. Edite .env con su llave (si aun no lo hizo)."
Write-Host "  2. Pruebe la llave:   .venv\Scripts\python.exe install\check_key.py"
Write-Host "============================================================"
