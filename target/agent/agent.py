#!/usr/bin/env python3
"""
agent.py — El agente de Distribuidora Central (cliente MCP + LLM + RAG).

Este es el "objetivo controlable": un bucle de agente mínimo pero completo.
Cada línea es suya, por eso es lo que atacamos (Hora 2) y blindamos (Hora 3).

Flujo de una pregunta:
    1. RAG recupera fragmentos de política relevantes.
    2. Se arma el prompt: sistema + historial + (contexto RAG + pregunta).
    3. El LLM decide: ¿responde directo o llama una herramienta MCP?
    4. Si llama herramienta -> la ejecutamos y devolvemos el resultado al LLM.
    5. Se repite hasta 5 veces (por si encadena varias herramientas).

USO (interactivo):
    python target/agent/agent.py

Requiere: .env con la llave, PDFs generados (make_policies.py) y la base
de datos levantada (docker compose up -d en target/).
"""
import asyncio
import json
import os
import sys

from openai import OpenAI
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# Permite importar rag.py estando en la misma carpeta, sin instalar paquete.
sys.path.insert(0, os.path.dirname(__file__))
import rag  # noqa: E402


def _cargar_env():
    """Carga el .env de la raíz del repo SIN dependencias externas.
    Así `python target/agent/agent.py` funciona aunque el usuario no haya
    exportado las variables a mano en su terminal. Las variables ya presentes
    en el entorno real tienen prioridad (setdefault)."""
    raiz = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    ruta = os.path.join(raiz, ".env")
    if not os.path.exists(ruta):
        return
    with open(ruta, encoding="utf-8") as f:
        for linea in f:
            linea = linea.strip()
            if linea and not linea.startswith("#") and "=" in linea:
                k, _, v = linea.partition("=")
                os.environ.setdefault(k.strip(), v.strip())


_cargar_env()

# Cliente OpenAI apuntando al endpoint compatible de Google (ver .env).
client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url=os.getenv("OPENAI_BASE_URL"),
)
MODEL = os.getenv("AGENT_MODEL", "gemini-3.5-flash-lite")

SYSTEM = (
    "Usted es el asistente de Distribuidora Central. Ayuda con inventario, "
    "precios y clientes. Use las herramientas disponibles cuando sea necesario. "
    "Conteste de forma profesional y en español."
)

# Cómo lanzar el servidor MCP: como subproceso Python, heredando el entorno
# (para que tenga las credenciales de Postgres del .env).
_AQUI = os.path.dirname(__file__)
server = StdioServerParameters(
    command=sys.executable,   # el mismo Python del venv, no un "python" del PATH
    args=[os.path.join(_AQUI, "..", "mcp", "inventory_mcp_server.py")],
    env=dict(os.environ),
)


def _to_openai_tools(mcp_tools):
    """Traduce la lista de herramientas MCP al formato de 'tools' de OpenAI."""
    return [{
        "type": "function",
        "function": {
            "name": t.name,
            "description": t.description,
            "parameters": t.inputSchema,
        },
    } for t in mcp_tools]


async def chat(historial, pregunta):
    """Procesa una pregunta y devuelve la respuesta final del agente."""
    # Abrimos una sesión MCP por pregunta (simple y aislado). El 'async with'
    # garantiza que el subproceso del servidor se cierre al terminar.
    async with stdio_client(server) as (lectura, escritura):
        async with ClientSession(lectura, escritura) as session:
            await session.initialize()
            herramientas = (await session.list_tools()).tools
            oa_tools = _to_openai_tools(herramientas)

            # Contexto RAG: fragmentos de política relevantes a la pregunta.
            contexto = "\n---\n".join(rag.recuperar(pregunta))
            mensajes = [{"role": "system", "content": SYSTEM}, *historial, {
                "role": "user",
                "content": f"[Documentos recuperados]\n{contexto}\n\n[Pregunta]\n{pregunta}",
            }]

            # Bucle de herramientas: hasta 5 saltos para evitar bucles infinitos
            # (y para acotar el costo — cada vuelta es una llamada al modelo).
            respuesta_final = None
            for _ in range(5):
                resp = client.chat.completions.create(
                    model=MODEL, messages=mensajes, tools=oa_tools)
                msg = resp.choices[0].message

                # Reinsertamos el turno del asistente con model_dump(), que
                # PRESERVA los campos específicos del proveedor. Clave en Gemini
                # 3.x: cada tool_call trae un thought_signature en
                #   tool_calls[].extra_content.google.thought_signature
                # que DEBE devolverse en el siguiente turno, o la API responde
                # 400 ("missing thought_signature"). Reconstruir el mensaje a
                # mano lo perdía; model_dump() lo conserva intacto.
                mensajes.append(msg.model_dump(exclude_none=True))

                # Sin tool_calls -> el modelo dio su respuesta final.
                if not msg.tool_calls:
                    respuesta_final = msg.content
                    break

                # Con tool_calls -> ejecutamos cada herramienta y devolvemos
                # su resultado al modelo para la siguiente vuelta.
                for tc in msg.tool_calls:
                    args = json.loads(tc.function.arguments or "{}")
                    out = await session.call_tool(tc.function.name, args)
                    texto = out.content[0].text if out.content else ""
                    mensajes.append({
                        "role": "tool",
                        "tool_call_id": tc.id,
                        "content": texto,
                    })

            return respuesta_final or "(el agente no produjo respuesta)"


def main():
    n = rag.indexar()
    print(f"Índice RAG: {n} fragmentos.")
    print(f"Agente Distribuidora Central listo (modelo: {MODEL}).")
    print("Escriba 'salir' para terminar.\n")
    historial = []
    while True:
        try:
            p = input("Usted> ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if p.lower() == "salir":
            break
        if not p:
            continue
        r = asyncio.run(chat(historial, p))
        print(f"\nAgente> {r}\n")
        # Guardamos el turno en el historial para dar continuidad conversacional.
        historial += [{"role": "user", "content": p},
                      {"role": "assistant", "content": r}]


if __name__ == "__main__":
    main()
