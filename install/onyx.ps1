# =============================================================================
#  onyx.ps1 — Ruta A: desplegar Onyx Standard y darle poder (Windows PowerShell)
# =============================================================================
#  Equivalente exacto de onyx.sh, para Windows. Automatiza lo mecánico de las
#  diapositivas 12-13:
#    1. Comprueba prerrequisitos (docker corriendo, git, .venv del taller).
#    2. Clona Onyx (proyecto aparte) junto al repo del taller.
#    3. Levanta Onyx Standard en Docker (RAG completo; ~16 GB RAM recomendados).
#    4. Levanta la base de datos del taller y genera los PDF de política.
#    5. Deja corriendo el servidor MCP en modo HTTP (le da herramientas a Onyx).
#    6. Imprime y guarda los valores EXACTOS para pegar en Onyx.
#
#  Lo que se hace en la UI de Onyx (conectar modelo, Acción MCP, subir PDF)
#  queda servido y explicado en  onyx-config.txt.
#
#  USO (desde la carpeta del repo):
#      powershell -ExecutionPolicy Bypass -File install\onyx.ps1
#
#  Requisito previo: haber corrido antes  install\setup.ps1  (crea .venv).
# =============================================================================
$ErrorActionPreference = "Stop"

# Raíz del repo del taller (un nivel arriba de \install).
$Raiz  = Split-Path -Parent $PSScriptRoot
Set-Location $Raiz
$Vpy   = Join-Path $Raiz ".venv\Scripts\python.exe"
# Onyx es un proyecto independiente: lo ponemos JUNTO al repo, no dentro.
$OnyxDir = Join-Path (Split-Path -Parent $Raiz) "onyx"
$Compose = Join-Path $OnyxDir "deployment\docker_compose"
# Standard = solo el compose base (Vespa + Redis + model-servers → RAG real).
# El overlay Lite quitaba esa pila y por eso el RAG citaba mal. ~16 GB de RAM.
$Base    = "docker-compose.yml"

Write-Host "==> Raiz del taller: $Raiz"
Write-Host "==> Onyx se instalara en: $OnyxDir"

# --- Paso 1: prerrequisitos ------------------------------------------------
Write-Host "`n==> [1/6] Comprobando prerrequisitos..."
$falta = $false
docker info *> $null
if ($LASTEXITCODE -eq 0) { Write-Host "    OK Docker esta corriendo" }
else { Write-Host "    FALTA: Docker no responde. Abra Docker Desktop y reintente."; $falta = $true }
if (Get-Command git -ErrorAction SilentlyContinue) { Write-Host "    OK $(git --version)" }
else { Write-Host "    FALTA git (obligatorio para clonar Onyx)"; $falta = $true }
if (Test-Path $Vpy) { Write-Host "    OK entorno del taller (.venv) listo" }
else { Write-Host "    FALTA .venv. Corra primero:  powershell -ExecutionPolicy Bypass -File install\setup.ps1"; $falta = $true }
if ($falta) { Write-Host "    Resuelva lo anterior y vuelva a ejecutar este script."; exit 1 }

# --- Paso 2: clonar Onyx ---------------------------------------------------
Write-Host "`n==> [2/6] Obteniendo Onyx..."
if (Test-Path $OnyxDir) {
  Write-Host "    Onyx ya esta clonado, lo reutilizo ($OnyxDir)."
} else {
  git clone --depth 1 https://github.com/onyx-dot-app/onyx.git $OnyxDir
  Write-Host "    OK clonado"
}

# El compose base podría cambiar de nombre entre versiones de Onyx.
$BasePath = Join-Path $Compose $Base
if (-not (Test-Path $BasePath)) {
  Write-Host "    FALTA '$Base' en $Compose"
  Write-Host "      El nombre pudo cambiar. Archivos compose disponibles:"
  Get-ChildItem (Join-Path $Compose "docker-compose*.yml") -ErrorAction SilentlyContinue | ForEach-Object { Write-Host "        $($_.Name)" }
  Write-Host "      Ajuste la variable `$Base en este script o vea docs\ONYX.md."
  exit 1
}

# --- Paso 3: levantar Onyx Standard ---------------------------------------
Write-Host "`n==> [3/6] Levantando Onyx Standard (RAG completo; ~16 GB RAM, descarga varios GB la 1a vez)..."
$OnyxEnv = Join-Path $Compose ".env"
if (-not (Test-Path $OnyxEnv)) {
  Copy-Item (Join-Path $Compose "env.template") $OnyxEnv
  Write-Host "    OK .env de Onyx creado (valores por defecto; no hay que editar nada)"
}
Push-Location $Compose
docker compose -f $Base up -d
Pop-Location
Write-Host "    OK Onyx arrancando. Standard tarda varios minutos (indexador + Vespa) en http://localhost:3000"

# --- Paso 4: base de datos del taller + PDFs -------------------------------
Write-Host "`n==> [4/6] Levantando la base de datos del taller y generando los PDF..."
Push-Location (Join-Path $Raiz "target")
docker compose up -d
Pop-Location
& $Vpy (Join-Path $Raiz "target\make_policies.py")
Write-Host "    OK base de datos arriba y PDF en target\policies\"

# --- Paso 5: valores para pegar en Onyx ------------------------------------
Write-Host "`n==> [5/6] Guardando la configuracion para pegar en Onyx..."
$Cfg = Join-Path $Raiz "onyx-config.txt"
$texto = @'
=============================================================================
 CONFIGURACION PARA PEGAR EN ONYX   (abra http://localhost:3000)
 Primero cree su cuenta de administrador local (correo + contrasena).
=============================================================================

1) MODELO (LLM) - Admin Panel > LLM > Add provider.
   *** Para que el agente LLAME a las herramientas MCP, use el proveedor
       NATIVO de Gemini, NO el "OpenAI-compatible". El endpoint compatible
       traduce mal las tool-calls y por eso daban error. ***
     Provider : Google Gemini   (si no aparece: Custom con "Provider Name" = gemini)
     API Key  : (su llave, empieza con AQ...)
     Model    : gemini-3.5-flash-lite   (sin prefijo; Onyx antepone "gemini/")
   Guardelo y marquelo como modelo por defecto.
   (Alternativa solo-chat / Ruta B CLI: OpenAI-compatible con
     Base URL: https://generativelanguage.googleapis.com/v1beta/openai/  y la misma llave.)

2) HERRAMIENTAS (Accion MCP) - Admin Panel > Actions > MCP Actions > Add MCP Server:
     Server URL : http://host.docker.internal:9000/mcp
       (En Linux, si no resuelve, use:  http://172.17.0.1:9000/mcp )
     Auth       : No Auth
   Pulse Connect y seleccione las tres herramientas:
       consultar_inventario, actualizar_stock, validar_enlace_proveedor

3) POLITICAS (RAG): suba los PDF de  target\policies\  como documentos,
   para que el agente los cite.

4) INSTRUCCION DE SISTEMA del asistente:
     Usted es el asistente de Distribuidora Central. Ayuda con inventario,
     precios y clientes. Use las herramientas disponibles cuando sea necesario.
     Conteste de forma profesional y en espanol.

-----------------------------------------------------------------------------
 Para apagar todo al terminar:
   cd ..\onyx\deployment\docker_compose ; docker compose -f docker-compose.yml down
   cd target ; docker compose down -v
   Y cierre la ventana del servidor MCP (Ctrl+C).
=============================================================================
'@
Set-Content -Path $Cfg -Value $texto -Encoding utf8
Write-Host "    OK guardada en: $Cfg"

# Abrimos el navegador (mejor esfuerzo).
Start-Process "http://localhost:3000" -ErrorAction SilentlyContinue

# --- Paso 6: servidor MCP en primer plano ----------------------------------
Write-Host "`n==> [6/6] Iniciando el servidor MCP (le da poder a Onyx)."
Write-Host ""
Write-Host "============================================================"
Write-Host " ESTA VENTANA ES AHORA EL SERVIDOR MCP. NO LA CIERRE."
Write-Host " Dejela abierta mientras use Onyx en http://localhost:3000"
Write-Host " Los valores para pegar en Onyx estan en: onyx-config.txt"
Write-Host "============================================================"
Write-Host ""
# Esta terminal se convierte en el proceso del servidor MCP.
& $Vpy (Join-Path $Raiz "target\mcp\inventory_mcp_server.py") --http
