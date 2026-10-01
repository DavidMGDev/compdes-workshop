# Taller COMPDES 2026 — Seguridad de Agentes MCP/RAG para PyMEs

Laboratorio práctico: construya un agente autónomo para una PyME ficticia
(*Distribuidora Central*), atáquelo con técnicas reales de *red teaming* y
luego blíndelo. Todo el código está aquí, comentado, para ejecutarlo y para
mostrarlo en vivo.

> **¿Primera vez, o partiendo de un PC en blanco?** Siga la
> **[Guía completa paso a paso](docs/GUIA_COMPLETA.md)**: instala todo desde cero
> (Python, Docker, Git) y llega hasta ver la demostración funcionando. Es la
> mejor puerta de entrada para cualquiera sin experiencia.

### Elija su ruta para la Hora 1

El agente se puede ejecutar de dos formas. **Ambas usan la misma base de datos
y las mismas herramientas MCP**, así que los ataques (Hora 2) y las defensas
(Hora 3) funcionan igual en las dos. Cada asistente elige según su equipo:

| | **Ruta A — Onyx** | **Ruta B — CLI ligero** |
|---|---|---|
| Qué es | [Onyx](https://onyx.app), plataforma de IA de código abierto: interfaz web de "producto" real | Un agente mínimo de terminal |
| Requisitos | Docker + **10 GB de RAM (16 recomendados)** y ~25 GB de disco | Solo Python + Docker |
| Guía | **[docs/ONYX.md](docs/ONYX.md)** | [docs/GUIA_COMPLETA.md](docs/GUIA_COMPLETA.md) |
| Cuándo | Laptop con músculo; quiere el efecto completo | Laptop justa; quiere lo más simple y estable |

Si Onyx no arranca en su equipo, pásese a la Ruta B **sin perder nada** del taller.

> **Aviso de uso responsable.** Todo esto se ejecuta **exclusivamente contra el
> laboratorio aislado que usted despliega en su máquina**. Las técnicas de
> inyección, SSRF y jailbreak son legítimas en *red teaming* de sistemas
> propios, pero ilegales contra sistemas de terceros.

---

## Estado: verificado el 30 de septiembre de 2026

El taller se impartió en **COMPDES, julio de 2026**. El 30-sep-2026 se volvió a
correr completo desde un clon limpio para confirmar que sigue funcionando con
las versiones de hoy de cada dependencia, y se le añadió una suite de pruebas
para poder repetir esa comprobación cuando haga falta.

- **24 pruebas** recorren las tres horas: la demo, cada ataque contra el agente
  vulnerable y el mismo ataque contra el agente blindado.
- **Costo medido de una pasada completa: $0.012.** Por asistente, entre 3 y 30
  centavos según cuánto repita (detalle en [`docs/PRESUPUESTO.md`](docs/PRESUPUESTO.md)).
- Qué se comprobó, qué hubo que actualizar y qué no se alcanzó a repasar:
  [`docs/VERIFICACION.md`](docs/VERIFICACION.md).

```bash
python -m unittest discover tests                 # sin gastar llave
TALLER_LIVE=1 python -m unittest discover tests   # + contra el modelo (~1.5 centavos)
```

---

## Estructura del taller

| Fase | Objetivo | Carpeta |
|---|---|---|
| **Hora 1 — Construir** | Desplegar el agente y ver su valor de negocio | `target/` |
| **Hora 2 — Romper** | Explotar el abuso de permisos legítimos | [`attacks/`](attacks/README.md) |
| **Hora 3 — Blindar** | Mitigar de forma pragmática para una PyME | [`defenses/`](defenses/README.md) |
| Comprobar | Que todo lo anterior sigue funcionando | `tests/` |

---

## Inicio rápido (instalador guiado)

**Requisitos previos:** Python 3.11+ (probado con 3.14), Docker, y (opcional, defensa 3.7) Node.js 22+.

### Linux / macOS
```bash
git clone https://github.com/DavidMGDev/compdes-workshop.git
cd compdes-workshop
bash install/setup.sh
```

### Windows (PowerShell)
```powershell
git clone https://github.com/DavidMGDev/compdes-workshop.git
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

Con el entorno virtual activado (`source .venv/bin/activate`; en Windows,
`.venv\Scripts\Activate.ps1`, o use `.venv\Scripts\python.exe` en lugar de `python`):

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

- [`docs/ONYX.md`](docs/ONYX.md) — **Ruta A:** correr el agente en Onyx (interfaz web) con sus herramientas MCP.
- [`docs/GUIA_COMPLETA.md`](docs/GUIA_COMPLETA.md) — **Ruta B:** del PC en blanco al agente CLI funcionando.
- [`docs/SETUP.md`](docs/SETUP.md) — instalación **manual** paso a paso (Windows + Linux).
- [`attacks/README.md`](attacks/README.md) — **Hora 2:** los cinco labs de ataque.
- [`defenses/README.md`](defenses/README.md) — **Hora 3:** las defensas y cómo comprobar cada una.
- [`docs/PRESUPUESTO.md`](docs/PRESUPUESTO.md) — modelos, precios reales, **costo medido** y control de gasto.
- [`docs/VERIFICACION.md`](docs/VERIFICACION.md) — la re-ejecución del 30-sep-2026: resultados y cambios.
- [`docs/guia_parte1.html`](docs/guia_parte1.html) — guía visual de la Parte 1 para asistentes.

## Limpieza (al terminar)

```bash
cd target && docker compose down -v      # apaga y borra la base de datos
```

---

## Nota sobre modelos

Todo el taller usa un único modelo, ya fijado en el `.env`:
**`gemini-3.5-flash-lite`** ($0.30/$2.50 por 1M tokens), el 3.5-class más
económico de Google, afinado para uso de herramientas. No hay que elegir nada.
El manual original mencionaba `gemini-3-flash`, un id que **no existe** (error
404, comprobado de nuevo el 30-sep-2026). Detalles en [`docs/PRESUPUESTO.md`](docs/PRESUPUESTO.md).
