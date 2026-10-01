# =============================================================================
#  onyx.ps1 — Ruta A: desplegar Onyx Standard y darle poder (Windows PowerShell)
# =============================================================================
#  Equivalente exacto de onyx.sh, para Windows. Automatiza lo mecánico de las
#  diapositivas 12-13:
#    1. Comprueba prerrequisitos (docker corriendo, git, .venv del taller).
#    2. Clona Onyx (proyecto aparte) junto al repo del taller.
#    3. Levanta Onyx Standard en Docker (RAG completo; 10 GB RAM minimo, 16 recomendados).
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
# Standard = solo el compose base (OpenSearch + Redis + model-servers → RAG real).
# El overlay Lite quitaba esa pila y por eso el RAG citaba mal. 10 GB de RAM minimo, 16 recomendados.
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
Write-Host "`n==> [3/6] Levantando Onyx Standard (RAG completo; descarga ~21 GB de imagenes la 1a vez)..."
$OnyxEnv = Join-Path $Compose ".env"
if (-not (Test-Path $OnyxEnv)) {
  Copy-Item (Join-Path $Compose "env.template") $OnyxEnv
  Write-Host "    OK .env de Onyx creado"
}
# Onyx exige USER_AUTH_SECRET: con el valor vacio de la plantilla, su servidor
# API se niega a arrancar. Generamos uno aleatorio (igual que onyx.sh).
$envTexto = Get-Content $OnyxEnv -Raw
if ($envTexto -match 'USER_AUTH_SECRET=""') {
  $bytes = New-Object byte[] 32
  [System.Security.Cryptography.RandomNumberGenerator]::Create().GetBytes($bytes)
  $secreto = -join ($bytes | ForEach-Object { $_.ToString("x2") })
  # WriteAllText: UTF-8 sin BOM y saltos de linea intactos (docker compose lo exige).
  [System.IO.File]::WriteAllText($OnyxEnv, $envTexto.Replace('USER_AUTH_SECRET=""', "USER_AUTH_SECRET=`"$secreto`""))
  Write-Host "    OK USER_AUTH_SECRET generado automaticamente en el .env de Onyx"
}
Push-Location $Compose
docker compose -f $Base up -d
Pop-Location
Write-Host "    OK Onyx arrancando. Standard tarda varios minutos (indexador + OpenSearch) en http://localhost:3000"

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

1) MODELO (LLM) - Admin Panel > Language Models > "Custom Models" > Set Up
     Provider     : gemini      (escriba "gemini" y elijalo en la lista)
     API Key      : (su llave de AI Studio)
     Display Name : Gemini
     Model Name   : gemini-3.5-flash-lite
   Pulse Connect. Queda como modelo por defecto.
   *** NO use la tarjeta "Gemini / Google Cloud Vertex AI": pide una cuenta de
       servicio de Google Cloud, no acepta la llave de AI Studio. ***

2) PERMITIR LA RED LOCAL - Admin Panel > Security & Hardening > Network Safety
     SSRF Protection : Allow Private Network
   (Por defecto, "Validate All Requests", Onyx se NIEGA a conectarse a su
    servidor MCP porque esta en una IP privada. Es la misma defensa anti-SSRF
    que usted construira en la Hora 3.)

3) HERRAMIENTAS (MCP) - Admin Panel > MCP Actions > Add MCP Server
     Server Name    : Distribuidora Central
     MCP Server URL : http://host.docker.internal:9000/mcp
   Pulse Add Server. En el dialogo siguiente:
     Authentication Method : None      -> Connect
   Deben aparecer 3 herramientas (3 of 3):
       consultar_inventario, actualizar_stock, validar_enlace_proveedor

4) AGENTE - en el chat: Agents > crear uno ("Asesor de Distribuidora")
     Instructions:
       Usted es el asistente de Distribuidora Central. Ayuda con inventario,
       precios y clientes. Use las herramientas disponibles cuando sea necesario.
       Conteste de forma profesional y en espanol.
     Actions: active "Distribuidora Central" (las 3 herramientas).
     Knowledge (opcional, RAG): suba los PDF de  target/policies/
   Pulse Create y chatee con ESE agente (el asistente por defecto no tiene
   las herramientas).

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
