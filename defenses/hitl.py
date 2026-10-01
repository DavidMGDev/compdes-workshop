#!/usr/bin/env python3
"""
hitl.py — Human-in-the-Loop: aprobación humana para acciones destructivas.
  Defiende: Lab 2.3 (Crescendo). | OWASP ASI mitigación de acciones irreversibles.

Integración en agent.py, dentro del bucle de herramientas, ANTES de
session.call_tool(...):

    from defenses.hitl import requiere_aprobacion
    if not requiere_aprobacion(tc.function.name, args):
        texto = "Acción cancelada por el operador."
    else:
        out = await session.call_tool(tc.function.name, args)
        texto = out.content[0].text if out.content else ""

Con esto, aunque el Crescendo "arrastre" al agente a un UPDATE masivo, la
acción exige que un humano escriba APROBAR. Se deniega y el ataque falla.
"""
import sys

# Herramientas cuyo efecto es irreversible o destructivo.
ACCIONES_DESTRUCTIVAS = {"actualizar_stock"}


def es_destructiva(nombre_herramienta: str, args: dict) -> bool:
    if nombre_herramienta in ACCIONES_DESTRUCTIVAS:
        return True
    # El servidor vulnerable acepta SQL libre por consultar_inventario: todo lo
    # que no sea UN solo SELECT (UPDATE, DELETE, DROP...) también es
    # destructivo. Es el camino del turno 5 del Crescendo.
    if nombre_herramienta == "consultar_inventario":
        sql = str(args.get("consulta_sql", "")).strip().rstrip(";").lower()
        return not sql.startswith("select") or ";" in sql
    return False


def requiere_aprobacion(nombre_herramienta: str, args: dict) -> bool:
    """Devuelve True si se puede ejecutar, False si el humano la rechaza.
    Las acciones no destructivas pasan sin preguntar."""
    if not es_destructiva(nombre_herramienta, args):
        return True
    # Sin un humano delante (wrapper HTTP, CI) no hay a quién preguntar: se
    # deniega. Fallar cerrado es la opción segura.
    if not sys.stdin or not sys.stdin.isatty():
        print(f"\n[DENEGADO: sin operador] {nombre_herramienta}({args})")
        return False
    print(f"\n[APROBACION REQUERIDA] {nombre_herramienta}({args})")
    respuesta = input("Escriba 'APROBAR' para ejecutar (cualquier otra cosa cancela): ")
    return respuesta.strip() == "APROBAR"


if __name__ == "__main__":
    # Auto-prueba: la lógica de decisión, sin depender del input interactivo.
    assert requiere_aprobacion("consultar_stock", {}) is True, "lo no-destructivo debe pasar"
    assert es_destructiva("actualizar_stock", {}), "el UPDATE debe estar vigilado"
    assert es_destructiva("consultar_inventario", {"consulta_sql": "UPDATE inventario SET stock=0;"})
    assert es_destructiva("consultar_inventario", {"consulta_sql": "SELECT 1; DELETE FROM clientes"})
    assert not es_destructiva("consultar_inventario", {"consulta_sql": "SELECT stock FROM inventario;"})
    print("hitl.py: auto-prueba OK (las consultas pasan; los UPDATE piden aprobación).")
