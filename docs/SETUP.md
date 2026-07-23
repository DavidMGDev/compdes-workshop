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
| Node.js | 20+ | *opcional*, solo Garak/Promptfoo (Horas 2-3) |

Compruebe:
```bash
python --version   # o python3 --version
docker --version
```

---

## Paso 1 — Obtener el código

```bash
git clone <URL-DEL-REPO> compdes-workshop
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
entrega el tutor y empieza con `AQ.`.

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
| `429 ... credits are depleted` | presupuesto del grupo agotado | avise al tutor |
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

## Limpieza

```bash
cd target && docker compose down -v     # apaga y borra datos
deactivate                              # sale del venv
```
