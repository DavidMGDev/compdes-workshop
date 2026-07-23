#!/usr/bin/env python3
"""
http_wrapper.py — Expone el agente por HTTP para las herramientas de red-teaming.

PyRIT (Lab 2.3), Garak (Lab 2.5) y Promptfoo (Lab 3.7) NO llaman a Gemini
directamente: atacan a ESTE wrapper, y el wrapper llama al agente. Así todas
las herramientas comparten un único punto de entrada y el mismo modelo.

  [ PyRIT / Garak / Promptfoo ]  --HTTP POST /chat-->  [ este wrapper ]  -->  agent.chat()

USO:
    # Arranca en http://localhost:8000
    python target/agent/http_wrapper.py

    # Para forzar el modelo barato en Garak (alto volumen), relance así:
    #   Linux/macOS:  AGENT_MODEL=gemini-3.5-flash-lite python target/agent/http_wrapper.py
    #   Windows PS:    $env:AGENT_MODEL="gemini-3.5-flash-lite"; python target/agent/http_wrapper.py

Contrato HTTP (lo que esperan las herramientas):
    POST /chat   {"pregunta": "..."}      -> {"respuesta": "..."}
    GET  /health                          -> {"ok": true, "modelo": "..."}
"""
import asyncio
import os
import sys

from fastapi import FastAPI
from pydantic import BaseModel

# Importamos el agente que ya escribimos (misma carpeta).
sys.path.insert(0, os.path.dirname(__file__))
import agent  # noqa: E402
import rag     # noqa: E402

app = FastAPI(title="Agente Distribuidora Central (wrapper)")

# Indexamos el RAG una sola vez, al arrancar el servidor (no por petición).
_INDEXADO = {"n": 0}


@app.on_event("startup")
def _startup():
    _INDEXADO["n"] = rag.indexar()
    print(f"[wrapper] RAG indexado: {_INDEXADO['n']} fragmentos. "
          f"Modelo: {agent.MODEL}")


class Peticion(BaseModel):
    # Aceptamos 'pregunta' (nuestro nombre) o 'prompt' (el que usan algunas
    # herramientas). Al menos uno debe venir.
    pregunta: str | None = None
    prompt: str | None = None


@app.get("/health")
def health():
    """Sonda de vida: útil para saber que el wrapper ya está listo."""
    return {"ok": True, "modelo": agent.MODEL, "fragmentos": _INDEXADO["n"]}


@app.post("/chat")
def chat(p: Peticion):
    """Recibe una pregunta, la pasa por el agente y devuelve la respuesta.

    Sin historial: cada petición es independiente. Es lo que quieren las
    herramientas de red-teaming (cada prueba parte de cero), salvo PyRIT
    Crescendo, que maneja su propio hilo multi-turno del lado atacante.
    """
    texto = p.pregunta or p.prompt or ""
    # agent.chat es asíncrono; lo corremos en un loop nuevo por petición.
    respuesta = asyncio.run(agent.chat([], texto))
    return {"respuesta": respuesta}


if __name__ == "__main__":
    import uvicorn
    # host 127.0.0.1: solo accesible desde esta máquina (no exponer a la red).
    uvicorn.run(app, host="127.0.0.1", port=8000)
