# Taller COMPDES 2026 — Seguridad de Agentes MCP/RAG para PyMEs

Laboratorio práctico: construya un agente autónomo para una PyME ficticia
(*Distribuidora Central*), atáquelo con técnicas reales de *red teaming* y
luego blíndelo. Todo el código está aquí, comentado, para ejecutarlo y para
mostrarlo en vivo.

> **Aviso de uso responsable.** Todo esto se ejecuta **exclusivamente contra el
> laboratorio aislado que usted despliega en su máquina**. Las técnicas de
> inyección, SSRF y jailbreak son legítimas en *red teaming* de sistemas
> propios, pero ilegales contra sistemas de terceros.

---

## Estructura del taller

| Fase | Objetivo | Carpeta |
|---|---|---|
| **Hora 1 — Construir** | Desplegar el agente y ver su valor de negocio | `target/` |
| **Hora 2 — Romper** | Explotar el abuso de permisos legítimos | `attacks/` |
| **Hora 3 — Blindar** | Mitigar de forma pragmática para una PyME | `defenses/` |

---

## Inicio rápido (instalador guiado)

**Requisitos previos:** Python 3.11+, Docker, y (opcional, Horas 2-3) Node.js.

### Linux / macOS
```bash
git clone <URL-DEL-REPO> compdes-workshop
cd compdes-workshop
bash install/setup.sh
```

### Windows (PowerShell)
```powershell
git clone <URL-DEL-REPO> compdes-workshop
cd compdes-workshop
powershell -ExecutionPolicy Bypass -File install\setup.ps1
```

El instalador: comprueba prerrequisitos → crea el entorno virtual → instala
dependencias → crea su `.env` → corre un diagnóstico.

### Luego
1. **Edite `.env`** y pegue su llave en `OPENAI_API_KEY` (se la da el tutor).
2. **Verifique la llave:**
   ```bash
   python install/check_key.py        # Linux/macOS
   .venv\Scripts\python.exe install\check_key.py   # Windows
   ```
   Debe imprimir `[OK] FUNCIONA`.

> ¿Prefiere hacerlo **a mano**, sin instalador? Siga [`docs/SETUP.md`](docs/SETUP.md)
> paso a paso. Es lo que se muestra en vivo en el taller.

---

## Hora 1 — Ver el valor (la demo)

```bash
# 1. Levante la base de datos de la PyME
cd target && docker compose up -d && cd ..

# 2. Genere los PDFs de política (para el RAG)
python target/make_policies.py

# 3. Arranque el agente
python target/agent/agent.py
```

Pruebe estas preguntas y observe al agente razonar, consultar la base y citar
políticas:

- `¿Cuánto stock tenemos de cemento?`
- `Según nuestra política, ¿qué crédito le doy a un cliente nuevo?`
- `Sube el stock del SKU-002 a 950.`

**Ese es el gancho:** un agente empresarial real, útil, en minutos. En la Hora 2
descubrirá que ese mismo poder es su superficie de ataque.

---

## Documentación

- [`docs/SETUP.md`](docs/SETUP.md) — instalación **manual** paso a paso (Windows + Linux).
- [`docs/PRESUPUESTO.md`](docs/PRESUPUESTO.md) — modelos, precios reales y control de gasto.
- [`docs/guia_parte1.html`](docs/guia_parte1.html) — guía visual de la Parte 1 para asistentes.

## Limpieza (al terminar)

```bash
cd target && docker compose down -v      # apaga y borra la base de datos
```

---

## Nota sobre modelos

Por defecto usamos **`gemini-2.5-flash-lite`** (el más económico). El manual
original mencionaba `gemini-3-flash`, un id que **no existe** (da error 404).
Detalles y precios reales en [`docs/PRESUPUESTO.md`](docs/PRESUPUESTO.md).
