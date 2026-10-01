#!/usr/bin/env python3
"""
pin_descriptors.py — Integridad y procedencia de descriptores MCP.
  Defiende: Lab 2.2 (Tool poisoning / rug pull).

IDEA: el modelo confía en la *descripción* de una herramienta como si la
hubiera escrito el desarrollador. Si un servidor MCP comprometido cambia esa
descripción DESPUÉS de que usted la aprobó (rug pull), inyecta instrucciones
con autoridad ambiental.

DEFENSA: fije (pin) el hash de los descriptores aprobados y recházelos si
cambian.

Integración en agent.py, tras list_tools() y antes de usarlas:
    from defenses.pin_descriptors import verificar
    verificar(herramientas)   # lanza RuntimeError si el descriptor cambió
"""
import hashlib
import json


def hash_tools(tools) -> str:
    """Hash estable (sort_keys) de nombre + descripción + esquema de cada tool.
    Los espacios de la descripción se normalizan: Python 3.13+ quita la sangría
    de las docstrings y las versiones anteriores no, y eso no es un ataque."""
    data = json.dumps(
        [{"n": t.name, "d": " ".join((t.description or "").split()), "s": t.inputSchema}
         for t in tools],
        sort_keys=True,
    )
    return hashlib.sha256(data.encode()).hexdigest()


# El hash de los descriptores REVISADOS Y APROBADOS. Este es el del servidor
# endurecido (defenses/inventory_mcp_server_seguro.py) tal como está en el repo.
# Si usted cambia una herramienta a propósito (o actualiza el paquete mcp y
# cambia el esquema generado), revise el cambio y pegue aquí el hash "actual"
# que imprime el error. Ese paso manual ES la defensa.
APROBADO = "35fe16753c9fe14a6543e235e43a2f3ff7701167f11147c8627f94d24568aa2d"


def verificar(tools) -> None:
    """Aborta el arranque si los descriptores no coinciden con lo aprobado."""
    actual = hash_tools(tools)
    if actual != APROBADO:
        raise RuntimeError(
            f"Descriptores MCP alterados: posible tool poisoning.\n"
            f"  esperado: {APROBADO}\n  actual:   {actual}\n"
            f"  (si el cambio es suyo y ya lo revisó, actualice APROBADO en "
            f"defenses/pin_descriptors.py)"
        )


if __name__ == "__main__":
    # Auto-prueba: un cambio en la descripción DEBE cambiar el hash.
    class T:  # stub mínimo con la forma de una tool MCP
        def __init__(self, n, d, s):
            self.name, self.description, self.inputSchema = n, d, s

    base = [T("consultar", "consulta inventario", {"type": "object"})]
    poison = [T("consultar", "consulta inventario <IMPORTANTE>...</IMPORTANTE>", {"type": "object"})]
    assert hash_tools(base) != hash_tools(poison), "el rug pull debe alterar el hash"
    print("pin_descriptors.py: auto-prueba OK (un descriptor alterado cambia el hash).")
