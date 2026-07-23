#!/usr/bin/env python3
"""
check_key.py — Verifica que su llave API funciona de extremo a extremo.

Hace UNA sola llamada barata al modelo y reporta el resultado en lenguaje
claro. Es la prueba definitiva de que su llave está lista para el taller.

USO:
    python install/check_key.py

Lee OPENAI_BASE_URL, OPENAI_API_KEY y AGENT_MODEL del entorno o del .env.
No instala nada: usa solo urllib de la librería estándar, así funciona
aunque todavía no haya creado el entorno virtual.
"""
import json
import os
import sys
import urllib.error
import urllib.request

# En Windows la consola suele ser cp1252 y rompe con acentos/símbolos.
# Forzamos UTF-8 con errors="replace": nunca lanza excepción, pase lo que pase.
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

# --- Carga mínima del .env (sin dependencias externas) --------------------
# Buscamos un .env en la raíz del repo y cargamos las variables que falten.
def cargar_env():
    raiz = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    ruta = os.path.join(raiz, ".env")
    if not os.path.exists(ruta):
        return
    with open(ruta, encoding="utf-8") as f:
        for linea in f:
            linea = linea.strip()
            if not linea or linea.startswith("#") or "=" not in linea:
                continue
            clave, _, valor = linea.partition("=")
            # No pisamos variables ya presentes en el entorno real.
            os.environ.setdefault(clave.strip(), valor.strip())


def main():
    cargar_env()
    base = os.environ.get("OPENAI_BASE_URL", "").rstrip("/")
    key = os.environ.get("OPENAI_API_KEY", "")
    modelo = os.environ.get("AGENT_MODEL", "gemini-2.5-flash-lite")

    # --- Validaciones antes de gastar una llamada -------------------------
    if not key or key == "PEGUE_SU_LLAVE_AQUI":
        print("[X] No hay llave. Edite el .env y pegue su llave en OPENAI_API_KEY.")
        sys.exit(1)
    if not base:
        print("[X] Falta OPENAI_BASE_URL en el .env.")
        sys.exit(1)
    if not key.startswith("AQ."):
        # No es fatal, pero sí sospechoso: las llaves modernas empiezan con AQ.
        print(f"[!] Su llave no empieza con 'AQ.' (empieza con '{key[:4]}...').")
        print("  Las llaves modernas de AI Studio empiezan con 'AQ.'. Continúo igual.")

    # --- La llamada de prueba (formato OpenAI chat completions) -----------
    url = f"{base}/chat/completions"
    cuerpo = json.dumps({
        "model": modelo,
        "messages": [{"role": "user", "content": "Responde solo con la palabra: listo"}],
    }).encode()
    req = urllib.request.Request(
        url, data=cuerpo, method="POST",
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
    )

    print(f"-> Probando modelo '{modelo}' ...")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.load(resp)
        texto = data["choices"][0]["message"]["content"].strip()
        uso = data.get("usage", {})
        print(f"[OK] FUNCIONA. El modelo respondió: {texto!r}")
        print(f"  Tokens usados: entrada={uso.get('prompt_tokens','?')} "
              f"salida={uso.get('completion_tokens','?')}")
        print("  Su llave está lista para el taller.")
        sys.exit(0)
    except urllib.error.HTTPError as e:
        # Traducimos los errores comunes a algo accionable.
        detalle = e.read().decode(errors="replace")
        try:
            msg = json.loads(detalle)["error"]["message"]
        except Exception:
            msg = detalle[:200]
        print(f"[X] Error HTTP {e.code}: {msg}")
        if e.code == 401:
            print("  -> La llave está mal copiada o incompleta. Cópiela de nuevo.")
        elif e.code == 429 and "credit" in msg.lower():
            print("  -> El presupuesto del grupo se agotó. Avise al tutor.")
        elif e.code == 429:
            print("  -> Límite de tasa: espere unos segundos y reintente.")
        elif e.code == 404:
            print(f"  -> El modelo '{modelo}' no existe. Revise AGENT_MODEL en el .env.")
        sys.exit(1)
    except Exception as e:
        print(f"[X] No se pudo conectar: {e}")
        print("  -> Revise su conexión a internet y OPENAI_BASE_URL.")
        sys.exit(1)


if __name__ == "__main__":
    main()
