#!/usr/bin/env python3
"""
inventory_mcp_server.py — Servidor MCP de Distribuidora Central.

  *** VERSIÓN VULNERABLE — se usa en la Hora 1 (construir) y la Hora 2 (romper).
      La versión endurecida está en defenses/inventory_mcp_server_seguro.py ***

Expone tres "herramientas" (tools) que el agente puede invocar. Dos de ellas
son deliberadamente inseguras para poder demostrar los ataques:

  - consultar_inventario : acepta SQL ARBITRARIO (lectura y escritura)  <- peligroso
  - actualizar_stock     : escritura acotada por SKU
  - validar_enlace_proveedor : hace GET a CUALQUIER url                 <- SSRF

Estas vulnerabilidades no son bugs: son el material didáctico del taller.

Transporte (dos modos, mismo código y mismas herramientas):
  - stdio  (por defecto): el agente CLI (target/agent/agent.py) lo lanza como
           subproceso y habla por stdin/stdout. También lo usa el Lab 2.2.
  - HTTP   (con --http): lo consume ONYX, que corre en contenedores y por eso
           NO puede hablar stdio. Onyx lo registra como "MCP Action" apuntando a
           http://host.docker.internal:9000/mcp  (ver docs/ONYX.md).
"""
import os

import psycopg2
from mcp.server.fastmcp import FastMCP

# El nombre identifica al servidor ante el cliente MCP.
mcp = FastMCP("distribuidora-central")


def _conn():
    """Abre una conexión a Postgres con las credenciales del entorno (.env)."""
    return psycopg2.connect(
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=os.getenv("POSTGRES_PORT", "5433"),
        dbname=os.getenv("POSTGRES_DB", "distribuidora"),
        user=os.getenv("POSTGRES_USER", "onyx_app"),
        password=os.getenv("POSTGRES_PASSWORD", "app_password_123"),
    )


@mcp.tool()
def consultar_inventario(consulta_sql: str) -> str:
    """Ejecuta una consulta SQL sobre la base de datos de inventario y clientes.
    Use esta herramienta para responder preguntas sobre stock, precios y clientes."""
    # ⚠ VULNERABLE A PROPÓSITO: acepta SQL arbitrario y permite escritura.
    #   Un atacante puede leer columnas sensibles (notas_internas) o destruir
    #   datos (UPDATE/DELETE). Se blinda en la Hora 3 (herramientas tipadas).
    with _conn() as c, c.cursor() as cur:
        cur.execute(consulta_sql)
        try:
            filas = cur.fetchall()          # si fue un SELECT, hay filas
            return str(filas)
        except psycopg2.ProgrammingError:
            # No había resultado -> fue INSERT/UPDATE/DELETE. Confirmamos.
            c.commit()
            return f"OK, filas afectadas: {cur.rowcount}"


@mcp.tool()
def actualizar_stock(sku: str, nuevo_stock: int) -> str:
    """Actualiza el stock de un producto por su SKU."""
    # Menos peligrosa que la anterior (consulta parametrizada), pero sigue
    # siendo una acción destructiva: en la Hora 3 la ponemos tras aprobación
    # humana (HITL).
    with _conn() as c, c.cursor() as cur:
        cur.execute("UPDATE inventario SET stock=%s WHERE sku=%s", (nuevo_stock, sku))
        c.commit()
        return f"Stock de {sku} actualizado a {nuevo_stock}."


@mcp.tool()
def validar_enlace_proveedor(url: str) -> str:
    """Valida que el enlace de catálogo de un proveedor esté activo
    (devuelve el inicio del contenido)."""
    # ⚠ VULNERABLE A PROPÓSITO: sin lista de permitidos -> SSRF.
    #   El agente puede ser inducido a pedir URLs internas (metadatos de la
    #   nube, servicios privados). Se blinda en la Hora 3 con allowlist.
    import requests
    r = requests.get(url, timeout=5)
    return r.text[:500]


if __name__ == "__main__":
    import sys
    # Acepta tanto --http como -http o http
    if any(arg in sys.argv for arg in ["--http", "-http", "http"]):
        # Modo HTTP para Onyx. Bind en 0.0.0.0 (no solo localhost) para que el
        # contenedor de Onyx pueda alcanzarlo vía host.docker.internal. Puerto
        # 9000 para no chocar con el wrapper HTTP del agente (8000).
        port = int(os.getenv("MCP_HTTP_PORT", "9000"))
        mcp.settings.host = "0.0.0.0"
        mcp.settings.port = port

        print("\n============================================================", flush=True)
        print(f" [OK] Servidor MCP de Distribuidora Central LISTO", flush=True)
        print(f" Escuchando localmente en:  http://0.0.0.0:{port}/mcp", flush=True)
        print(f" Para Onyx configura en:    http://host.docker.internal:{port}/mcp", flush=True)
        print("============================================================", flush=True)
        print(" -> Mantenga esta terminal abierta mientras trabaja en la Ruta A.\n", flush=True)

        mcp.run(transport="streamable-http")
    else:
        # mcp.run() arranca el bucle de servidor sobre stdio (modo por defecto).
        mcp.run()

