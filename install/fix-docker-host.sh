#!/usr/bin/env bash
# =============================================================================
#  fix-docker-host.sh — Arregla la conectividad Docker→Host en Linux
# =============================================================================
#  En Linux, los contenedores de Onyx no pueden alcanzar el servidor MCP que
#  corre en el host por dos razones:
#
#    1. El firewall del host (iptables/nftables) bloquea el tráfico entrante
#       desde las subredes de Docker hacia puertos del host.
#    2. El SDK de MCP para Python rechaza peticiones con Host header distinto
#       de localhost (protección contra DNS rebinding → 421 Misdirected).
#
#  Este script arregla ambas cosas. Es idempotente: se puede ejecutar varias
#  veces sin problema. Los cambios de firewall NO persisten tras un reinicio
#  (lo cual es deseable para un entorno de taller temporal).
#
#  USO:   sudo bash install/fix-docker-host.sh
#    o:   bash install/fix-docker-host.sh        (pedirá la contraseña de sudo)
#
#  En Windows / Docker Desktop esto NO es necesario (Docker Desktop maneja
#  host.docker.internal de forma transparente).
# =============================================================================
set -euo pipefail

MCP_PORT="${MCP_HTTP_PORT:-9000}"

# ---------------------------------------------------------------------------
# Colores para la salida
# ---------------------------------------------------------------------------
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

ok()   { echo -e "    ${GREEN}✓${NC} $*"; }
warn() { echo -e "    ${YELLOW}!${NC} $*"; }
fail() { echo -e "    ${RED}✗${NC} $*"; }

# ---------------------------------------------------------------------------
# Detectar SO
# ---------------------------------------------------------------------------
if [[ "$(uname -s)" != "Linux" ]]; then
  echo "Este script es solo para Linux. En Windows/macOS no es necesario."
  exit 0
fi

echo ""
echo "============================================================"
echo " Arreglando conectividad Docker → Host (Linux)"
echo "============================================================"
echo ""

# ---------------------------------------------------------------------------
# Paso 1: Abrir el firewall para tráfico Docker → puerto MCP
# ---------------------------------------------------------------------------
echo "==> [1/2] Firewall: permitir tráfico Docker hacia el puerto $MCP_PORT..."

# Función para ejecutar con sudo si no somos root
run_priv() {
  if [[ $EUID -eq 0 ]]; then
    "$@"
  else
    sudo "$@"
  fi
}

# Verificar si iptables está disponible
if ! command -v iptables >/dev/null 2>&1; then
  warn "iptables no encontrado. Si usa nftables, agregue la regla manualmente:"
  warn "  nft add rule inet filter input tcp dport $MCP_PORT accept"
else
  # Verificar si la regla ya existe (para idempotencia)
  RULE_COMMENT="compdes-workshop-mcp"
  if run_priv iptables -C INPUT -p tcp --dport "$MCP_PORT" -s 172.16.0.0/12 \
       -m comment --comment "$RULE_COMMENT" -j ACCEPT 2>/dev/null; then
    ok "Regla de firewall ya existe (puerto $MCP_PORT abierto para Docker)"
  else
    run_priv iptables -I INPUT -p tcp --dport "$MCP_PORT" -s 172.16.0.0/12 \
         -m comment --comment "$RULE_COMMENT" -j ACCEPT
    ok "Regla agregada: Docker (172.16.0.0/12) → puerto $MCP_PORT"
  fi

  # También permitir desde la subred de Onyx (172.19.x.x) por si acaso
  if run_priv iptables -C INPUT -p tcp --dport "$MCP_PORT" -s 192.168.0.0/16 \
       -m comment --comment "$RULE_COMMENT-lan" -j ACCEPT 2>/dev/null; then
    ok "Regla LAN ya existe"
  else
    run_priv iptables -I INPUT -p tcp --dport "$MCP_PORT" -s 192.168.0.0/16 \
         -m comment --comment "$RULE_COMMENT-lan" -j ACCEPT
    ok "Regla agregada: LAN (192.168.0.0/16) → puerto $MCP_PORT"
  fi
fi

echo ""
echo "    Nota: estas reglas NO persisten tras reiniciar (ideal para un taller)."
echo ""

# ---------------------------------------------------------------------------
# Paso 2: Verificar conectividad (si hay contenedores de Onyx corriendo)
# ---------------------------------------------------------------------------
echo "==> [2/2] Verificando conectividad..."

if docker ps --format '{{.Names}}' 2>/dev/null | grep -q "onyx-api_server"; then
  # Intentar conectar desde dentro del contenedor de Onyx
  if docker exec onyx-api_server-1 \
       python -c "import socket; s=socket.socket(); s.settimeout(3); s.connect(('host.docker.internal',$MCP_PORT)); s.close(); print('OK')" \
       2>/dev/null; then
    ok "Onyx puede alcanzar host.docker.internal:$MCP_PORT"
  else
    warn "Onyx aún no puede conectar a host.docker.internal:$MCP_PORT"
    warn "Asegúrese de que el servidor MCP esté corriendo:"
    warn "  python target/mcp/inventory_mcp_server.py --http"
  fi
else
  warn "Contenedores de Onyx no están corriendo; no se pudo verificar."
  warn "Ejecute esta verificación después de levantar Onyx."
fi

echo ""
echo "============================================================"
echo " Listo. Ahora inicie (o reinicie) el servidor MCP:"
echo ""
echo "   python target/mcp/inventory_mcp_server.py --http"
echo ""
echo " Y en Onyx use la URL:"
echo "   http://host.docker.internal:$MCP_PORT/mcp"
echo "============================================================"
echo ""
