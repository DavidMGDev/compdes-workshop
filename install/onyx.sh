#!/usr/bin/env bash
# =============================================================================
#  onyx.sh — Ruta A: desplegar Onyx Lite y darle poder (Linux / macOS)
# =============================================================================
#  Automatiza lo mecánico de las diapositivas 12–13 del taller:
#    1. Comprueba prerrequisitos (docker corriendo, git, .venv del taller).
#    2. Clona Onyx (proyecto aparte) junto al repo del taller.
#    3. Levanta Onyx Lite en Docker (~2 GB RAM).
#    4. Levanta la base de datos del taller y genera los PDF de política.
#    5. Deja corriendo el servidor MCP en modo HTTP (le da herramientas a Onyx).
#    6. Imprime y guarda los valores EXACTOS para pegar en Onyx.
#
#  Lo que NO se puede automatizar (se hace en la UI de Onyx, este script se lo
#  deja servido y explicado): conectar el modelo, registrar la Acción MCP y
#  subir los PDF. Los pasos y valores quedan en  onyx-config.txt.
#
#  USO:   bash install/onyx.sh
#
#  Requisito previo: haber corrido antes  bash install/setup.sh  (crea .venv).
# =============================================================================
set -euo pipefail

# Nos ubicamos en la raíz del repo del taller, venga de donde venga la invocación.
cd "$(dirname "$0")/.."
RAIZ="$(pwd)"
VPY="$RAIZ/.venv/bin/python"
# Onyx es un proyecto independiente: lo ponemos JUNTO al repo, no dentro.
ONYX_DIR="$(dirname "$RAIZ")/onyx"
COMPOSE="$ONYX_DIR/deployment/docker_compose"
LITE="docker-compose.onyx-lite.yml"

echo "==> Raíz del taller: $RAIZ"
echo "==> Onyx se instalará en: $ONYX_DIR"

# --- Paso 1: prerrequisitos ------------------------------------------------
echo ""
echo "==> [1/6] Comprobando prerrequisitos..."
falta=0
DOCKER_ERR=$(docker info 2>&1 || true)
if echo "$DOCKER_ERR" | grep -q "Server Version"; then
  echo "    ✓ Docker está corriendo"
elif echo "$DOCKER_ERR" | grep -q "permission denied"; then
  echo "    ✗ Permiso denegado para conectarse a Docker."
  echo "      Ejecute este comando en su terminal para activar los permisos de grupo y reintente:"
  echo "        newgrp docker"
  echo "      (O si usa Fish shell:  exec sg docker fish)"
  falta=1
else
  echo "    ✗ Docker no responde. Arránquelo (sudo systemctl start docker) y reintente."
  falta=1
fi
if command -v git >/dev/null 2>&1; then
  echo "    ✓ $(git --version)"
else
  echo "    ✗ git no está instalado (obligatorio para clonar Onyx)"; falta=1
fi
if [ -x "$VPY" ]; then
  echo "    ✓ entorno del taller (.venv) listo"
else
  echo "    ✗ falta .venv. Corra primero:  bash install/setup.sh"; falta=1
fi
if [ "$falta" -ne 0 ]; then
  echo "    Resuelva lo anterior y vuelva a ejecutar este script."
  exit 1
fi

# --- Paso 2: clonar Onyx ---------------------------------------------------
echo ""
echo "==> [2/6] Obteniendo Onyx..."
if [ -d "$ONYX_DIR" ]; then
  echo "    Onyx ya está clonado, lo reutilizo ($ONYX_DIR)."
else
  git clone --depth 1 https://github.com/onyx-dot-app/onyx.git "$ONYX_DIR"
  echo "    ✓ clonado"
fi

# Verificamos que exista el archivo de modo Lite (el nombre podría cambiar
# entre versiones de Onyx; si cambia, avisamos en vez de fallar en seco).
if [ ! -f "$COMPOSE/$LITE" ]; then
  echo "    ✗ No encontré '$LITE' en $COMPOSE"
  echo "      El nombre pudo cambiar. Archivos compose disponibles:"
  ls "$COMPOSE"/docker-compose*.yml 2>/dev/null || true
  echo "      Ajuste la variable LITE en este script o vea docs/ONYX.md."
  exit 1
fi

# --- Paso 3: levantar Onyx Lite -------------------------------------------
echo ""
echo "==> [3/6] Levantando Onyx Lite (la primera vez descarga cientos de MB)..."
if [ ! -f "$COMPOSE/.env" ]; then
  cp "$COMPOSE/env.template" "$COMPOSE/.env"
  echo "    ✓ .env de Onyx creado"
fi
# Onyx requiere USER_AUTH_SECRET obligatorio para iniciar el servidor API
if grep -q 'USER_AUTH_SECRET=""' "$COMPOSE/.env" || ! grep -q 'USER_AUTH_SECRET=' "$COMPOSE/.env"; then
  SECRET=$(openssl rand -hex 32 2>/dev/null || echo "onyx_secret_workshop_key_$(date +%s)")
  sed -i "s/USER_AUTH_SECRET=\"\"/USER_AUTH_SECRET=\"$SECRET\"/g" "$COMPOSE/.env"
  echo "    ✓ USER_AUTH_SECRET generado automáticamente en .env de Onyx"
fi
( cd "$COMPOSE" && docker compose -f docker-compose.yml -f "$LITE" up -d )
echo "    ✓ Onyx arrancando. Tarda ~1–2 min en estar listo en http://localhost:3000"

# --- Paso 4: base de datos del taller + PDFs -------------------------------
echo ""
echo "==> [4/6] Levantando la base de datos del taller y generando los PDF..."
( cd "$RAIZ/target" && docker compose up -d )
"$VPY" "$RAIZ/target/make_policies.py"
echo "    ✓ base de datos arriba y PDF en target/policies/"

# --- Paso 5: valores para pegar en Onyx ------------------------------------
echo ""
echo "==> [5/6] Guardando la configuración para pegar en Onyx..."
CFG="$RAIZ/onyx-config.txt"
cat > "$CFG" <<'TXT'
=============================================================================
 CONFIGURACIÓN PARA PEGAR EN ONYX   (abra http://localhost:3000)
 Primero cree su cuenta de administrador local (correo + contraseña).
=============================================================================

1) MODELO (LLM) — Admin Panel > LLM > Add provider (OpenAI-compatible):
     Base URL : https://generativelanguage.googleapis.com/v1beta/openai/
     API Key  : (su llave, empieza con AQ...)
     Model    : gemini-3.5-flash-lite
   Guárdelo y márquelo como modelo por defecto.

2) HERRAMIENTAS (Acción MCP) — Admin Panel > Actions > MCP Actions > Add MCP Server:
     Server URL : http://host.docker.internal:9000/mcp
       (En Linux, si no resuelve, use:  http://172.17.0.1:9000/mcp )
     Auth       : No Auth
   Pulse Connect y seleccione las tres herramientas:
       consultar_inventario, actualizar_stock, validar_enlace_proveedor

3) POLÍTICAS (RAG): suba los PDF de  target/policies/  como documentos,
   para que el agente los cite.

4) INSTRUCCIÓN DE SISTEMA del asistente:
     Usted es el asistente de Distribuidora Central. Ayuda con inventario,
     precios y clientes. Use las herramientas disponibles cuando sea necesario.
     Conteste de forma profesional y en español.

-----------------------------------------------------------------------------
 Para apagar todo al terminar:
   (cd ../onyx/deployment/docker_compose && docker compose -f docker-compose.yml -f docker-compose.onyx-lite.yml down)
   (cd target && docker compose down -v)
   Y cierre la ventana del servidor MCP (Ctrl+C).
=============================================================================
TXT
echo "    ✓ guardada en: $CFG"

# Intentamos abrir el navegador (mejor esfuerzo; no es crítico).
( command -v xdg-open >/dev/null 2>&1 && xdg-open http://localhost:3000 >/dev/null 2>&1 & ) || true
( command -v open     >/dev/null 2>&1 && open     http://localhost:3000 >/dev/null 2>&1 & ) || true

# --- Paso 6: servidor MCP en primer plano ----------------------------------
echo ""
echo "==> [6/6] Iniciando el servidor MCP (le da poder a Onyx)."
echo ""
echo "============================================================"
echo " ESTA VENTANA ES AHORA EL SERVIDOR MCP. NO LA CIERRE."
echo " Déjela abierta mientras use Onyx en http://localhost:3000"
echo " Los valores para pegar en Onyx están en: onyx-config.txt"
echo "============================================================"
echo ""
# exec: esta terminal se convierte en el proceso del servidor MCP.
exec "$VPY" "$RAIZ/target/mcp/inventory_mcp_server.py" --http
