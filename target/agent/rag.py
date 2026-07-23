#!/usr/bin/env python3
"""
rag.py — RAG mínimo sobre los PDFs de política.

RAG = Retrieval-Augmented Generation. Antes de preguntarle al modelo,
recuperamos los fragmentos de documento más parecidos a la pregunta y se los
damos como contexto. Así el agente "cita" las políticas de la PyME.

Es intencionalmente simple (embeddings en memoria, sin base vectorial): el
objetivo es enseñar, no escalar. Para 2-3 PDFs sobra.
"""
import glob
import os

import numpy as np
from sentence_transformers import SentenceTransformer

# Modelo de embeddings pequeño y rápido (~90 MB). Se descarga la 1ª vez.
_model = SentenceTransformer("all-MiniLM-L6-v2")

# Estado del índice, en memoria: los fragmentos de texto y sus vectores.
_chunks: list[str] = []
_emb: np.ndarray | None = None

# Carpeta de PDFs por defecto (relativa a la raíz del repo).
_CARPETA = os.path.join(os.path.dirname(__file__), "..", "policies")


def indexar(carpeta: str = _CARPETA) -> int:
    """Lee los PDFs de `carpeta`, los trocea por párrafos y calcula embeddings.
    Devuelve cuántos fragmentos indexó."""
    global _chunks, _emb
    _chunks = []
    for path in glob.glob(os.path.join(carpeta, "*.pdf")):
        # Import local: pdfplumber es pesado; solo lo cargamos al indexar.
        import pdfplumber
        with pdfplumber.open(path) as pdf:
            texto = "\n".join((p.extract_text() or "") for p in pdf.pages)
        # Troceo simple: un fragmento por párrafo no vacío.
        for parr in (t.strip() for t in texto.split("\n\n")):
            if parr:
                _chunks.append(parr)
    if not _chunks:
        _emb = None
        return 0
    # normalize_embeddings=True permite usar producto punto como similitud coseno.
    _emb = _model.encode(_chunks, normalize_embeddings=True)
    return len(_chunks)


def recuperar(pregunta: str, k: int = 3) -> list[str]:
    """Devuelve los `k` fragmentos más parecidos a la pregunta."""
    if _emb is None or not _chunks:
        return []
    q = _model.encode([pregunta], normalize_embeddings=True)[0]
    sims = _emb @ q                      # similitud coseno con cada fragmento
    idx = np.argsort(-sims)[:k]          # los k índices de mayor similitud
    return [_chunks[i] for i in idx]


if __name__ == "__main__":
    # Auto-prueba: indexa y hace una consulta de ejemplo.
    n = indexar()
    print(f"Fragmentos indexados: {n}")
    if n:
        print("Prueba 'credito':", recuperar("plazo de credito para cliente nuevo")[:1])
