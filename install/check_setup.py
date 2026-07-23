#!/usr/bin/env python3
"""
check_setup.py — Diagnóstico del entorno del taller (SIN gastar la llave).

Verifica todo lo que se puede verificar sin llamar al modelo:
prerrequisitos instalados, estructura de archivos, .env bien formado y
dependencias de Python importables. Úselo antes de check_key.py.

USO:
    python install/check_setup.py

Solo usa la librería estándar, así corre aunque el venv no exista todavía.
Sale con código 0 si todo está OK, 1 si hay algún fallo bloqueante.
"""
import importlib.util
import os
import shutil
import subprocess
import sys

# En Windows la consola suele ser cp1252 y rompe con acentos/símbolos.
# Forzamos UTF-8 con errors="replace": nunca lanza excepción, pase lo que pase.
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
fallos = 0   # contador de problemas bloqueantes


# Marcadores ASCII: la consola de Windows (cp1252) no puede imprimir ✓/✗ y
# lanzaría UnicodeEncodeError. ASCII funciona en TODA terminal, sin trucos.
def ok(msg):    print(f"  [OK]   {msg}")
def warn(msg):  print(f"  [!]    {msg}")
def bad(msg):
    global fallos
    fallos += 1
    print(f"  [X]    {msg}")


def version_de(cmd, args=("--version",)):
    """Devuelve la primera línea de `cmd --version`, o None si no existe."""
    exe = shutil.which(cmd)
    if not exe:
        return None
    try:
        out = subprocess.run([exe, *args], capture_output=True, text=True, timeout=15)
        return (out.stdout or out.stderr).strip().splitlines()[0]
    except Exception:
        return None


# --- 1. Prerrequisitos del sistema ---------------------------------------
print("\n[1/4] Prerrequisitos del sistema")
# Python es obligatorio; el resto depende de qué parte del taller haga.
py = f"{sys.version_info.major}.{sys.version_info.minor}"
if sys.version_info >= (3, 11):
    ok(f"Python {py}")
else:
    bad(f"Python {py} — se requiere 3.11 o superior")

for cmd, obligatorio in [("docker", True), ("git", True), ("node", False)]:
    v = version_de(cmd)
    if v:
        ok(v)
    elif obligatorio:
        bad(f"'{cmd}' no está instalado (obligatorio)")
    else:
        warn(f"'{cmd}' no está instalado (opcional: solo para labs de Garak/Promptfoo)")


# --- 2. Estructura de archivos del repo ----------------------------------
print("\n[2/4] Estructura del repositorio")
esperados = [
    "requirements.txt",
    ".env.example",
    "target/docker-compose.yml",
    "target/seed.sql",
    "target/agent/agent.py",
    "target/mcp/inventory_mcp_server.py",
]
for rel in esperados:
    if os.path.exists(os.path.join(RAIZ, rel)):
        ok(rel)
    else:
        bad(f"falta {rel}")


# --- 3. El archivo .env ---------------------------------------------------
print("\n[3/4] Configuración (.env)")
env_path = os.path.join(RAIZ, ".env")
if not os.path.exists(env_path):
    bad(".env no existe — cópielo de .env.example y pegue su llave")
else:
    valores = {}
    with open(env_path, encoding="utf-8") as f:
        for linea in f:
            linea = linea.strip()
            if linea and not linea.startswith("#") and "=" in linea:
                k, _, v = linea.partition("=")
                valores[k.strip()] = v.strip()
    if valores.get("OPENAI_API_KEY", "PEGUE_SU_LLAVE_AQUI") in ("", "PEGUE_SU_LLAVE_AQUI"):
        bad("OPENAI_API_KEY sin configurar en el .env")
    else:
        ok("OPENAI_API_KEY presente")
        if not valores["OPENAI_API_KEY"].startswith("AQ."):
            warn("la llave no empieza con 'AQ.' (las modernas sí lo hacen)")
    for req in ("OPENAI_BASE_URL", "AGENT_MODEL"):
        if valores.get(req):
            ok(f"{req} = {valores[req]}")
        else:
            bad(f"falta {req} en el .env")


# --- 4. Dependencias de Python -------------------------------------------
print("\n[4/4] Dependencias de Python")
# Comprobamos si son importables en ESTE intérprete. Si corre check_setup.py
# con el venv activado, valida el venv; si no, valida el Python del sistema.
paquetes = {
    "openai": "openai", "mcp": "mcp", "pydantic": "pydantic",
    "pdfplumber": "pdfplumber", "reportlab": "reportlab",
    "sentence_transformers": "sentence-transformers", "numpy": "numpy",
    "requests": "requests", "fastapi": "fastapi", "uvicorn": "uvicorn",
}
faltan = [pip for mod, pip in paquetes.items()
          if importlib.util.find_spec(mod) is None]
if not faltan:
    ok("todas las dependencias base están instaladas")
else:
    warn(f"faltan {len(faltan)}: {', '.join(faltan)}")
    warn("ejecute el instalador (setup.sh / setup.ps1) o: pip install -r requirements.txt")


# --- Veredicto ------------------------------------------------------------
print("\n" + "=" * 60)
if fallos == 0:
    print("RESULTADO: entorno OK. Ahora pruebe su llave:  python install/check_key.py")
    sys.exit(0)
else:
    print(f"RESULTADO: {fallos} problema(s) bloqueante(s). Resuélvalos y reintente.")
    sys.exit(1)
