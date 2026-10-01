# Instalación manual, paso a paso (sin instalador)

Esta guía hace **a mano** exactamente lo mismo que `install/setup.sh` /
`install/setup.ps1`. Sírvase de ella para mostrar el montaje en vivo, o si
prefiere no correr scripts automáticos.

Cada paso indica la versión **Linux/macOS** y la versión **Windows PowerShell**.

---

## Paso 0 — Prerrequisitos

Necesita, instalados y en el PATH:

| Herramienta | Versión | Para qué |
|---|---|---|
| Python | 3.11+ | todo el código del taller |
| Docker | 24+ | la base de datos y (Hora 1) Onyx |
| Node.js | 22+ | *opcional*, solo Promptfoo (defensa 3.7) |

Compruebe:
```bash
python --version   # o python3 --version
docker --version
```

---

## Paso 1 — Obtener el código

```bash
git clone https://github.com/DavidMGDev/compdes-workshop.git
cd compdes-workshop
```

---

## Paso 2 — Entorno virtual de Python

Aísla las dependencias del taller del resto de su sistema.

**Linux / macOS:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

**Windows PowerShell:**
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
# Si PowerShell bloquea el script de activación, use directamente el intérprete:
#   .venv\Scripts\python.exe   en lugar de   python
```

---

## Paso 3 — Instalar dependencias

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

> `sentence-transformers` arrastra PyTorch: la primera instalación descarga
> varios cientos de MB y tarda unos minutos. Es normal.

---

## Paso 4 — Configurar la llave (`.env`)

**Linux / macOS:**
```bash
cp .env.example .env
```
**Windows PowerShell:**
```powershell
Copy-Item .env.example .env
```

Abra `.env` en un editor y pegue su llave en `OPENAI_API_KEY`. La llave se la
entrega el tutor (empieza con `AQ.`; las llaves antiguas, con `AIza`).

> **Nunca** suba `.env` a git. Ya está en `.gitignore`.

---

## Paso 5 — Verificar

Dos comprobaciones. La primera no gasta la llave; la segunda hace una llamada
real barata.

```bash
python install/check_setup.py    # prerrequisitos, estructura, .env, dependencias
python install/check_key.py      # llamada real: debe decir "[OK] FUNCIONA"
```

Si `check_key.py` dice `[OK] FUNCIONA`, está listo.

### Errores comunes

| Mensaje | Causa | Solución |
|---|---|---|
| `401 UNAUTHENTICATED` | llave mal copiada | cópiela completa, sin espacios |
| `402` o `429 ... credits are depleted` | presupuesto del grupo agotado | avise al tutor |
| `404 ... model` | `AGENT_MODEL` inválido | revise el nombre en `.env` |
| `ModuleNotFoundError` | venv no activado o deps sin instalar | repita pasos 2 y 3 |

---

## Paso 6 — Levantar el laboratorio (Hora 1)

```bash
# Base de datos de la PyME
cd target
docker compose up -d
docker compose ps          # debe verse "healthy"
cd ..

# PDFs de política para el RAG
python target/make_policies.py

# El agente
python target/agent/agent.py
```

---

## Paso 7 — Comprobar que todo el taller funciona (opcional)

La suite de `tests/` recorre el taller completo. Con la base arriba y el venv
activado:

```bash
python -m unittest discover tests            # sin gastar llave (~1 min)
TALLER_LIVE=1 python -m unittest discover tests   # + Hora 1, ataques y defensas contra el modelo (~1.5 centavos)
python tests/costo.py                        # cuánto costó, por fase
```
En PowerShell, la segunda línea es `$env:TALLER_LIVE="1"; python -m unittest discover tests`.

## Entornos aparte para las Horas 2 y 3

- **Garak (Lab 2.5):** va en su propio venv con Python 3.11–3.13; ver
  [`../attacks/README.md`](../attacks/README.md).
- **Promptfoo (defensa 3.7):** no se instala; se corre con `npx` (Node.js 22+);
  ver [`../defenses/README.md`](../defenses/README.md).

---

## Limpieza

```bash
cd target && docker compose down -v     # apaga y borra datos
deactivate                              # sale del venv
```
