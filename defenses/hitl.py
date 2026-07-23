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

# Herramientas cuyo efecto es irreversible o destructivo.
ACCIONES_DESTRUCTIVAS = {"actualizar_stock", "eliminar_producto", "actualizar_credito"}


def requiere_aprobacion(nombre_herramienta: str, args: dict) -> bool:
    """Devuelve True si se puede ejecutar, False si el humano la rechaza.
    Las acciones no destructivas pasan sin preguntar."""
    if nombre_herramienta not in ACCIONES_DESTRUCTIVAS:
        return True
    print(f"\n[APROBACION REQUERIDA] {nombre_herramienta}({args})")
    respuesta = input("Escriba 'APROBAR' para ejecutar (cualquier otra cosa cancela): ")
    return respuesta.strip() == "APROBAR"


if __name__ == "__main__":
    # Auto-prueba: la lógica de decisión, sin depender del input interactivo.
    assert requiere_aprobacion("consultar_stock", {}) is True, "lo no-destructivo debe pasar"
    assert "actualizar_stock" in ACCIONES_DESTRUCTIVAS, "el UPDATE debe estar vigilado"
    print("hitl.py: auto-prueba OK (las consultas pasan; los UPDATE piden aprobación).")
