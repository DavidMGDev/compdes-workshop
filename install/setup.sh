#!/usr/bin/env bash
# =============================================================================
#  setup.sh — Instalador guiado del taller (Linux / macOS)
# =============================================================================
#  Qué hace, paso a paso (puede hacerlo A MANO siguiendo docs/SETUP.md):
#    1. Comprueba prerrequisitos (python3, docker).
#    2. Crea un entorno virtual de Python (.venv).
#    3. Instala las dependencias base.
#    4. Crea el .env a partir de la plantilla si no existe.
#    5. Corre el diagnóstico (check_setup.py).
#
#  USO:   bash install/setup.sh
#
#  Es intencionalmente simple y verboso: cada paso se imprime para que usted
#  vea exactamente qué se ejecuta. No hay magia oculta.
# =============================================================================
set -euo pipefail   # aborta ante el primer error; falla si se usa variable sin definir

# Nos ubicamos en la raíz del repo, sin importar desde dónde se invoque.
cd "$(dirname "$0")/.."
RAIZ="$(pwd)"
echo "==> Raíz del taller: $RAIZ"

# --- Paso 1: prerrequisitos ------------------------------------------------
echo ""
echo "==> [1/5] Comprobando prerrequisitos..."
falta=0
if command -v python3 >/dev/null 2>&1; then
  echo "    ✓ $(python3 --version)"
else
  echo "    ✗ python3 no está instalado (obligatorio)"; falta=1
fi
if command -v docker >/dev/null 2>&1; then
  echo "    ✓ $(docker --version)"
else
  echo "    ✗ docker no está instalado (obligatorio para el laboratorio)"; falta=1
fi
if [ "$falta" -ne 0 ]; then
  echo "    Instale lo que falta y vuelva a ejecutar este script."
  exit 1
fi

# --- Paso 2: entorno virtual ----------------------------------------------
echo ""
echo "==> [2/5] Creando entorno virtual (.venv)..."
if [ -d .venv ]; then
  echo "    .venv ya existe, lo reutilizo."
else
  python3 -m venv .venv
  echo "    ✓ creado"
fi
# 'source' activa el venv en ESTA sesión del script.
# shellcheck disable=SC1091
source .venv/bin/activate

# --- Paso 3: dependencias --------------------------------------------------
echo ""
echo "==> [3/5] Instalando dependencias (puede tardar varios minutos)..."
python -m pip install --upgrade pip >/dev/null
python -m pip install -r requirements.txt
echo "    ✓ dependencias instaladas"

# --- Paso 4: archivo .env --------------------------------------------------
echo ""
echo "==> [4/5] Configurando .env..."
if [ -f .env ]; then
  echo "    .env ya existe, no lo toco."
else
  cp .env.example .env
  echo "    ✓ .env creado a partir de la plantilla."
  echo "    >>> AHORA edite .env y pegue su llave en OPENAI_API_KEY <<<"
fi

# --- Paso 5: diagnóstico ---------------------------------------------------
echo ""
echo "==> [5/5] Diagnóstico del entorno..."
python install/check_setup.py || true   # informa, no aborta el instalador

echo ""
echo "============================================================"
echo "Instalación terminada."
echo "Siguientes pasos:"
echo "  1. Edite .env con su llave (si aún no lo hizo)."
echo "  2. Active el entorno:   source .venv/bin/activate"
echo "  3. Pruebe la llave:     python install/check_key.py"
echo "============================================================"
