#!/usr/bin/env python3
"""
costo.py — ¿Cuánto costó? Convierte un registro de uso a dólares.

El agente anota los tokens de cada llamada al modelo cuando la variable
USAGE_LOG apunta a un archivo (ver _registrar_uso en target/agent/agent.py).
Las pruebas en vivo lo activan solas (tests/uso.log).

USO:
    python tests/costo.py                 # lee tests/uso.log
    python tests/costo.py otro.log        # o el registro que usted indique

Para medir su propia sesión:
    Linux/macOS:  USAGE_LOG=mi-sesion.log python target/agent/agent.py
    Windows PS:   $env:USAGE_LOG="mi-sesion.log"; python target\\agent\\agent.py
"""
import collections
import json
import os
import sys

# Dólares por 1M de tokens (entrada, salida). Fuente: ai.google.dev/pricing,
# consultado el 30-sep-2026. Si cambia el precio, cambie esta línea.
PRECIOS = {"gemini-3.5-flash-lite": (0.30, 2.50)}


def resumir(ruta):
    """Devuelve {fase: [llamadas, tokens_entrada, tokens_salida, dolares]}."""
    fases = collections.defaultdict(lambda: [0, 0, 0, 0.0])
    with open(ruta, encoding="utf-8") as f:
        for linea in f:
            d = json.loads(linea)
            p_in, p_out = PRECIOS[d["modelo"]]
            fila = fases[d.get("fase") or "(sin fase)"]
            fila[0] += 1
            fila[1] += d["entrada"]
            fila[2] += d["salida"]
            fila[3] += (d["entrada"] * p_in + d["salida"] * p_out) / 1e6
    return fases


if __name__ == "__main__":
    ruta = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(__file__), "uso.log")
    fases = resumir(ruta)
    print(f"{'fase':<62}{'llamadas':>9}{'entrada':>10}{'salida':>9}{'USD':>10}")
    for nombre, (n, ent, sal, usd) in fases.items():
        print(f"{nombre:<62}{n:>9}{ent:>10}{sal:>9}{usd:>10.5f}")
    n, ent, sal, usd = (sum(f[i] for f in fases.values()) for i in range(4))
    print(f"{'TOTAL':<62}{n:>9}{ent:>10}{sal:>9}{usd:>10.5f}")
