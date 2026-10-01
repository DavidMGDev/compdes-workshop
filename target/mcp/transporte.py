#!/usr/bin/env python3
"""
transporte.py — Arranque común de los servidores MCP del taller.

Lo comparten el servidor vulnerable (target/mcp/inventory_mcp_server.py) y el
endurecido (defenses/inventory_mcp_server_seguro.py), para que AMBOS se puedan
servir igual:

  - stdio  (por defecto): el agente CLI lo lanza como subproceso.
  - HTTP   (con --http): lo consume ONYX, que corre en contenedores y por eso
           NO puede hablar stdio. Onyx lo registra como "MCP Action" apuntando a
           http://host.docker.internal:9000/mcp  (ver docs/ONYX.md).
"""
import os
import sys

from mcp.server.transport_security import TransportSecuritySettings


def servir(mcp):
    """Arranca `mcp` en stdio, o en HTTP/SSE si se pasó --http / --sse."""
    use_sse = any(arg in sys.argv for arg in ["--sse", "-sse", "sse"])
    use_http = any(arg in sys.argv for arg in ["--http", "-http", "http"])

    if not (use_http or use_sse):
        # mcp.run() arranca el bucle de servidor sobre stdio (modo por defecto).
        mcp.run()
        return

    port = int(os.getenv("MCP_HTTP_PORT", "9000"))
    mcp.settings.host = "0.0.0.0"
    mcp.settings.port = port
    transport_mode = "sse" if use_sse else "streamable-http"
    endpoint_path = "/sse" if use_sse else "/mcp"

    # Permitir conexiones desde contenedores Docker (Onyx) además de localhost.
    # Sin esto, el middleware de seguridad DNS rebinding rechaza las peticiones
    # con Host: host.docker.internal o Host: 172.x.x.x con 421 Misdirected.
    mcp.settings.transport_security = TransportSecuritySettings(
        enable_dns_rebinding_protection=True,
        allowed_hosts=[
            "127.0.0.1:*",
            "localhost:*",
            "[::1]:*",
            "host.docker.internal:*",   # Docker Desktop / Linux host-gateway
            "172.17.0.1:*",             # docker0 bridge gateway
            "172.19.0.1:*",             # onyx_default bridge gateway
            f"0.0.0.0:{port}",          # bind address
        ],
        allowed_origins=[
            "http://127.0.0.1:*",
            "http://localhost:*",
            "http://[::1]:*",
            "http://host.docker.internal:*",
            "http://172.17.0.1:*",
            "http://172.19.0.1:*",
        ],
    )

    print("\n============================================================", flush=True)
    print(f" [OK] Servidor MCP '{mcp.name}' LISTO ({transport_mode})", flush=True)
    print(f" Escuchando localmente en:  http://0.0.0.0:{port}{endpoint_path}", flush=True)
    print(f" URL para Onyx:             http://host.docker.internal:{port}{endpoint_path}", flush=True)
    print(f" (Si falla en Linux prueba): http://172.17.0.1:{port}{endpoint_path}", flush=True)
    print("============================================================", flush=True)
    print(" -> Mantenga esta terminal abierta mientras trabaja en la Ruta A.\n", flush=True)

    mcp.run(transport=transport_mode)
