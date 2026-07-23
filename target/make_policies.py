#!/usr/bin/env python3
"""
make_policies.py — Genera los PDFs de política para el RAG.

El agente responde preguntas de negocio citando estos documentos. En un caso
real serían las políticas internas de la PyME; aquí los generamos ficticios.

USO:
    python target/make_policies.py

Crea target/policies/*.pdf. Ejecútelo una vez antes de arrancar el agente.
"""
import os
import sys

from reportlab.pdfgen import canvas

# UTF-8 seguro en la consola de Windows (evita UnicodeEncodeError con acentos).
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

# Carpeta de salida (relativa a la raíz del repo). La creamos si no existe.
DESTINO = os.path.join(os.path.dirname(__file__), "policies")
os.makedirs(DESTINO, exist_ok=True)


def pdf(nombre, lineas):
    """Escribe un PDF de una página con las líneas de texto dadas."""
    ruta = os.path.join(DESTINO, nombre)
    c = canvas.Canvas(ruta)
    y = 800                       # coordenada vertical inicial (puntos)
    for linea in lineas:
        c.drawString(50, y, linea)
        y -= 20                   # bajamos 20 puntos por línea
    c.save()
    print(f"  [OK] {ruta}")


print("Generando PDFs de política...")
pdf("credito.pdf", [
    "POLITICA DE CREDITO",
    "El plazo maximo de credito para clientes nuevos es de 30 dias.",
    "El monto maximo inicial es de 5000 dolares.",
])
pdf("descuentos.pdf", [
    "POLITICA DE DESCUENTOS",
    "Descuento por volumen: 5% arriba de 100 unidades.",
])
print("Listo. Ahora puede arrancar el agente.")
