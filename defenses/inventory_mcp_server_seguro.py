#!/usr/bin/env python3
"""
inventory_mcp_server_seguro.py — Servidor MCP ENDURECIDO (Hora 3).

Versión defendida del servidor de target/mcp/. Cambios clave:

  - Nada de SQL arbitrario: herramientas TIPADAS con consultas parametrizadas
    (defiende 2.1 exfiltración y 2.3 destrucción vía SQL libre).
  - URLs con lista de permitidos + bloqueo de rangos privados/metadatos
    (defiende 2.4 SSRF).

Para usarlo en vivo: en agent.py cambie la ruta del servidor MCP de
target/mcp/inventory_mcp_server.py a este archivo, y repita los ataques 2.1/2.4:
ahora fallan.
"""
import ipaddress
import os
import socket
from urllib.parse import urlparse

import psycopg2
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("distribuidora-central-segura")


def _conn_readonly():
    """Conexión con un rol de SOLO LECTURA (ver defenses/roles_seguros.sql).
    Aunque secuestren el agente, esta identidad no puede escribir ni leer
    columnas sensibles."""
    return psycopg2.connect(
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=os.getenv("POSTGRES_PORT", "5433"),
        dbname=os.getenv("POSTGRES_DB", "distribuidora"),
        user=os.getenv("POSTGRES_RO_USER", "lector"),
        password=os.getenv("POSTGRES_RO_PASSWORD", "lector_pwd"),
    )


# --- (a) Herramientas tipadas: sin SQL libre -----------------------------
@mcp.tool()
def consultar_stock(sku: str) -> str:
    """Devuelve el stock de un SKU (solo lectura, consulta parametrizada)."""
    with _conn_readonly() as c, c.cursor() as cur:
        # %s parametrizado: imposible inyectar SQL por el valor de sku.
        cur.execute("SELECT producto, stock FROM inventario WHERE sku=%s", (sku,))
        fila = cur.fetchone()
        return str(fila) if fila else f"SKU {sku} no encontrado."


# --- (b) URL con allowlist + bloqueo de IPs internas ---------------------
PERMITIDOS = {"catalogos.proveedor-confiable.com"}


def _url_segura(url: str) -> bool:
    """True solo si la URL es https, está en la allowlist y NO resuelve a una
    IP privada/loopback/link-local (bloquea 169.254.169.254, localhost, etc.)."""
    p = urlparse(url)
    if p.scheme != "https" or p.hostname not in PERMITIDOS:
        return False
    try:
        ip = ipaddress.ip_address(socket.gethostbyname(p.hostname))
        return not (ip.is_private or ip.is_link_local or ip.is_loopback)
    except Exception:
        return False


@mcp.tool()
def validar_enlace_proveedor(url: str) -> str:
    """Valida un enlace de catálogo SOLO de proveedores en lista de permitidos."""
    if not _url_segura(url):
        return "RECHAZADO: URL fuera de la lista de permitidos."
    import requests
    return requests.get(url, timeout=5).text[:500]


if __name__ == "__main__":
    mcp.run()
