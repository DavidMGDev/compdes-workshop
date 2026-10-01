#!/usr/bin/env python3
"""
inventory_mcp_server_seguro.py — Servidor MCP ENDURECIDO (Hora 3).

Versión defendida del servidor de target/mcp/. Cambios clave:

  - Nada de SQL arbitrario: herramientas TIPADAS con consultas parametrizadas
    (defiende 2.1 exfiltración y 2.3 destrucción vía SQL libre).
  - URLs con lista de permitidos + bloqueo de rangos privados/metadatos
    (defiende 2.4 SSRF).
  - Cada herramienta se conecta con el rol de MÍNIMO privilegio que necesita
    (defensa 3.5). Requiere haber aplicado antes defenses/roles_seguros.sql.

Para usarlo en vivo: en agent.py cambie la ruta del servidor MCP de
target/mcp/inventory_mcp_server.py a este archivo, y repita los ataques 2.1/2.4:
ahora fallan. (defenses/agent_seguro.py ya lo trae hecho.)

Igual que el vulnerable, acepta --http para registrarlo en Onyx (Ruta A).
"""
import ipaddress
import os
import socket
import sys
from urllib.parse import urlparse

import psycopg2
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("distribuidora-central-segura")


def _conn(user, password):
    return psycopg2.connect(
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=os.getenv("POSTGRES_PORT", "5433"),
        dbname=os.getenv("POSTGRES_DB", "distribuidora"),
        user=user, password=password,
    )


def _conn_readonly():
    """Conexión con un rol de SOLO LECTURA (ver defenses/roles_seguros.sql).
    Aunque secuestren el agente, esta identidad no puede escribir ni leer
    columnas sensibles."""
    return _conn(os.getenv("POSTGRES_RO_USER", "lector"),
                 os.getenv("POSTGRES_RO_PASSWORD", "lector_pwd"))


# --- (a) Herramientas tipadas: sin SQL libre -----------------------------
@mcp.tool()
def consultar_stock(sku: str) -> str:
    """Devuelve el stock de un SKU (solo lectura, consulta parametrizada)."""
    with _conn_readonly() as c, c.cursor() as cur:
        # %s parametrizado: imposible inyectar SQL por el valor de sku.
        cur.execute("SELECT producto, stock FROM inventario WHERE sku=%s", (sku,))
        fila = cur.fetchone()
        return str(fila) if fila else f"SKU {sku} no encontrado."


@mcp.tool()
def buscar_producto(nombre: str) -> str:
    """Busca productos por nombre (p. ej. 'cemento') y devuelve SKU, producto,
    stock y precio de venta. Solo lectura."""
    with _conn_readonly() as c, c.cursor() as cur:
        # El patrón también va parametrizado. Y solo columnas no sensibles:
        # el rol 'lector' ni siquiera tiene permiso sobre costo_unit.
        cur.execute("SELECT sku, producto, stock, precio_unit FROM inventario "
                    "WHERE producto ILIKE %s", (f"%{nombre}%",))
        return str(cur.fetchall())


@mcp.tool()
def actualizar_stock(sku: str, nuevo_stock: int) -> str:
    """Actualiza el stock de un producto por su SKU (requiere aprobación humana)."""
    if nuevo_stock < 0:
        return "RECHAZADO: el stock no puede ser negativo."
    # Rol que SOLO puede hacer UPDATE de la columna stock. El agente la pone
    # además tras aprobación humana (defenses/hitl.py).
    with _conn(os.getenv("POSTGRES_RW_USER", "escritor_stock"),
               os.getenv("POSTGRES_RW_PASSWORD", "escritor_pwd")) as c, c.cursor() as cur:
        cur.execute("UPDATE inventario SET stock=%s WHERE sku=%s", (nuevo_stock, sku))
        c.commit()
        return (f"Stock de {sku} actualizado a {nuevo_stock}." if cur.rowcount
                else f"SKU {sku} no encontrado.")


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
    # Sin seguir redirecciones: un host permitido no puede "rebotar" hacia dentro.
    return requests.get(url, timeout=5, allow_redirects=False).text[:500]


if __name__ == "__main__":
    # Mismo arranque que el servidor vulnerable: stdio, o HTTP con --http.
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "target", "mcp"))
    from transporte import servir
    servir(mcp)
