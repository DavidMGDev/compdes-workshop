# Cambios por el modelo de dos rutas (Onyx como foco) — resumen para la presentación

Documento de trabajo para **actualizar la presentación (PowerPoint)**. No es
material de asistente; es el mapa de qué cambió, cómo reorientar cada hora hacia
**Onyx** como propuesta de valor, y cómo lograr que todo corra perfecto en
**Windows y Linux**.

> **Idea central para las diapositivas.** El taller ahora **abre con Onyx**: una
> PyME puede tener, en minutos, un agente de IA con **interfaz de producto real**
> que consulta su base de datos y cita sus políticas. Ese es el gancho comercial.
> Recién cuando el público ve el valor, mostramos que ese mismo poder es la
> superficie de ataque (Hora 2) y cómo blindarlo sin frenar el negocio (Hora 3).

---

## 1. Qué cambió en el repositorio (ya hecho)

| Cambio | Archivo | Por qué importa para la presentación |
|---|---|---|
| Servidor MCP **dual-transporte** (stdio + `--http`) | `target/mcp/inventory_mcp_server.py` | Onyx corre en contenedores y **no habla stdio**; ahora expone las herramientas por HTTP en `:9000/mcp` para que Onyx las use. |
| Guía completa de la ruta Onyx | `docs/ONYX.md` | Es el guion técnico de la Hora 1 (y de dónde caen los ataques en Onyx). |
| Elección de **dos rutas** | `README.md`, `docs/GUIA_COMPLETA.md` | Cada asistente elige: **Ruta A (Onyx)** o **Ruta B (CLI ligero)**. Ambas comparten DB y herramientas MCP. |
| Paso Onyx alineado | `docs/guia_parte1.html` | La guía visual ahora refleja el flujo real (Admin Panel, MCP Action). |
| `mcp>=1.8` | `requirements.txt` | Necesario para el transporte `streamable-http` que consume Onyx. |
| Fila de troubleshooting para shells no-bash (fish/csh) | `docs/GUIA_COMPLETA.md` | Evita el falso "error" de `source .venv/bin/activate` en Linux. |
| Onyx **Standard** en vez de Lite | `install/onyx.sh`, `install/onyx.ps1`, `docs/ONYX.md` | Lite no traía la pila de indexado (Vespa) → el RAG citaba mal. Standard da RAG real. Cuesta ~16 GB RAM (laptops flojas → Ruta B). |
| Modelo en Onyx = Gemini **nativo**, no OpenAI-compatible | `docs/ONYX.md`, `onyx-config.txt` | El endpoint OpenAI-compatible de Google traduce mal las *tool-calls* y el agente erraba al llamar herramientas MCP. El proveedor nativo `gemini/` sí las ejecuta. |
| Script `install/fix-docker-host.sh` + allowlist de hosts en el servidor MCP | `install/fix-docker-host.sh`, `target/mcp/inventory_mcp_server.py` | En Linux el firewall bloqueaba Docker→host y el SDK de MCP rechazaba el `Host` de Docker (421). El script abre el puerto y el server acepta `host.docker.internal`/`172.x`. |

**Sin pérdidas:** la Ruta B (agente CLI `target/agent/agent.py`) sigue intacta
como respaldo para laptops sin músculo. **Los ataques y defensas son idénticos**
en ambas rutas porque comparten la misma base de datos y el mismo servidor MCP.

---

## 2. Cómo enfocar cada hora en Onyx

### Hora 1 — Construir / el valor (100 % Onyx)

**Mensaje:** "Su PyME puede tener esto hoy." Onyx es el protagonista.

1. Abrir **`http://localhost:3000`** — se ve una interfaz de chat de producto,
   no una terminal. Ese contraste vende solo.
2. Mostrar que el agente está configurado con: **su modelo (Gemini)**, **sus
   documentos (RAG sobre los PDF de política)** y **sus herramientas (MCP)**.
3. Las tres preguntas de la demo, en vivo en el chat:
   - `¿Cuánto stock tenemos de cemento?` → consulta la base de datos.
   - `¿Qué crédito le doy a un cliente nuevo según la política?` → **cita el PDF**.
   - `Sube el stock del SKU-002 a 950.` → **modifica** la base de datos.

**Diapositiva de cierre de Hora 1:** el diagrama de `docs/ONYX.md`
(Onyx → Acción MCP → herramientas → PostgreSQL). Deja claro que Onyx no es "solo
un chat": **actúa** sobre datos reales. Eso prepara la Hora 2.

> Para laptops flojas: la **Ruta B (CLI)** hace exactamente lo mismo en terminal.
> No es un plan B de peor calidad; es el mismo agente sin la capa de UI.

### Hora 2 — Romper (atacar a Onyx directamente)

**Mensaje:** "El atacante no rompe la contraseña; abusa de permisos legítimos."
Se ataca **el chat de Onyx**, no un script.

| Lab | En Onyx (para la diapositiva) |
|---|---|
| 2.1 Inyección vía RAG | Subir un **PDF envenenado** como documento y hacer una pregunta inocente. |
| 2.2 Tool poisoning | Envenenar la *descripción* de la herramienta MCP; Onyx la relee y obedece. |
| 2.3 Crescendo | Jailbreak **multi-turno** directo en el chat de Onyx. |
| 2.4 SSRF | Pedirle a Onyx "validar" una URL interna; dispara la herramienta vulnerable. |
| 2.5 Garak/PyRIT | Escaneo automatizado contra la API de Onyx (o el wrapper HTTP). |

**Punto clave para la diapositiva:** el ataque viaja por un canal **legítimo**
(un documento, la descripción de una herramienta, una conversación normal). Onyx
lo hace más real porque es un producto que una PyME sí desplegaría.

### Hora 3 — Blindar (arreglar a Onyx sin romper el negocio)

**Mensaje:** "Autoridad acotada por acción, no un principal todopoderoso."

1. Cambiar el servidor MCP vulnerable por el **endurecido**
   (`defenses/inventory_mcp_server_seguro.py`), relanzarlo en `--http` y
   **re-registrar la Acción MCP en Onyx**.
2. **Repetir cada ataque en Onyx** → ahora falla. Esa repetición en vivo es la
   prueba visual más fuerte del taller.
3. Los tres controles mínimos para PyMEs (router + herramientas tipadas + HITL)
   se explican como "lo que sí puede aplicar una PyME el lunes".

**Diapositiva de cierre:** la matriz ataque → defensa de `defenses/README.md`,
pero encuadrada como "cómo blindar el agente Onyx que mostramos en la Hora 1".

---

## 3. Que corra perfecto en Windows y Linux

Esta es la sección más importante para la logística de 21 laptops.

### Común a ambos sistemas
- **Docker debe estar corriendo** antes de todo (en Windows: Docker Desktop en
  "Engine running").
- **Descargar imágenes ANTES del taller** (las de Onyx pesan varios cientos de MB).
  No dejarlo para el día con 21 personas y un wifi.
- **RAM:** Onyx Standard necesita ~16 GB libres (RAG completo). Quien no los tenga → Ruta B.

### Windows
- Instalar con `winget` (Python, Git, Docker Desktop). Reabrir PowerShell tras instalar.
- Docker Desktop puede pedir **WSL2**; aceptar.
- El instalador del taller: `powershell -ExecutionPolicy Bypass -File install\setup.ps1`.
- Onyx: `install.sh` es de shell; en Windows usar el `docker compose -f docker-compose.yml up -d` **explícito** (Standard, sin overlay Lite) desde PowerShell o Git Bash.
- `host.docker.internal` **funciona de fábrica** en Docker Desktop → la Acción MCP
  usa `http://host.docker.internal:9000/mcp` sin ajustes.

### Linux
- `apt install` de Python/Docker; `usermod -aG docker $USER` y **reiniciar sesión**.
- Shell **fish/zsh**: `source .venv/bin/activate` puede fallar. Solución robusta:
  llamar al Python del entorno directo (`.venv/bin/python ...`) sin activar.
- `host.docker.internal` a veces **no resuelve** dentro del contenedor. Usar la IP
  del bridge: `http://172.17.0.1:9000/mcp` en la Acción MCP.
- Archivos `.sh` con finales de línea LF (ya forzado por `.gitattributes`).

### Tabla rápida de "gotchas" (para una diapositiva de troubleshooting)

| Síntoma | Sistema | Solución |
|---|---|---|
| `source ... activate` → `case ... not inside switch` | Linux (fish) | `.venv/bin/python archivo.py` (sin activar) |
| Onyx no ve las herramientas MCP | Linux | Cambiar `host.docker.internal` por `172.17.0.1` |
| Onyx no ve las herramientas MCP | Ambos | ¿Está corriendo `inventory_mcp_server.py --http`? |
| `docker: daemon not running` | Ambos | Encender Docker (Desktop en Windows) |
| Onyx muy lento / se cae | Ambos | Falta RAM → usar Ruta B (CLI) |
| Puerto 3000 / 5433 / 9000 ocupado | Ambos | Cerrar el proceso o cambiar el puerto |

---

## 4. Guion sugerido de diapositivas (esqueleto)

1. **Portada** — Seguridad de agentes MCP/RAG para PyMEs.
2. **El problema** — las PyMEs quieren IA que actúe sobre sus datos, no solo chatee.
3. **La solución (demo Onyx)** — captura de `localhost:3000` respondiendo las 3 preguntas.
4. **Qué hay debajo** — diagrama Onyx → MCP → PostgreSQL. "Un agente que actúa."
5. **Elija su ruta** — Onyx (completa) vs CLI (ligera); misma esencia.
6. **Transición** — "ese poder es también la superficie de ataque".
7–11. **Hora 2** — un ataque por diapositiva, mostrado en Onyx (tabla del §2).
12. **La lección** — no se rompió la auth; se abusó de permisos legítimos.
13–15. **Hora 3** — los 3 controles mínimos; repetir ataques en Onyx → fallan.
16. **Matriz ataque → defensa.**
17. **Cierre** — "lo que una PyME puede desplegar y blindar el lunes".
18. **Glosario / recursos** (ver `docs/glosario.html`).

---

## 5. Glosario de tecnologías (qué es, cuándo se usa, relación con Onyx)

Versión visual y navegable: **`docs/glosario.html`**. Resumen aquí:

| Tecnología | Para qué sirve aquí | Cuándo | Relación con Onyx |
|---|---|---|---|
| **Onyx (Lite, CE)** | La plataforma de IA con UI web: el agente de la PyME | Hora 1 (y 2-3) | **Es el núcleo** |
| **Gemini `gemini-3.5-flash-lite`** | El modelo (cerebro) que razona y decide | Todo el taller | **Núcleo** (Onyx lo usa) |
| **Endpoint compatible con OpenAI** | El "idioma" con que Onyx y el código hablan con Gemini | Todo | **Núcleo** (así se configura Onyx) |
| **MCP (Model Context Protocol)** | El estándar para darle herramientas al agente | Hora 1-3 | **Núcleo** (Acción MCP de Onyx) |
| **FastMCP** | La librería que implementa el servidor MCP | Hora 1-3 | **Núcleo** (sirve a Onyx en `:9000/mcp`) |
| **PostgreSQL** | La base de datos de la PyME (los "datos joya") | Todo | Soporte (Onyx la consulta vía MCP; Lite guarda su estado ahí) |
| **RAG (sentence-transformers)** | Recuperar y citar los PDF de política | Hora 1-2 | **Núcleo** (Onyx trae RAG integrado) |
| **Docker / Docker Compose** | Levanta la base de datos **y Onyx** en contenedores | Setup + todo | **Núcleo** (Onyx corre sobre Docker) |
| **reportlab / pdfplumber** | Generar / leer los PDF de política | Hora 1 | Soporte (los PDF se suben a Onyx) |
| **Git / GitHub** | Descargar el taller **y clonar Onyx** | Setup | Soporte |
| **OWASP Agentic Top 10 (ASI)** | Taxonomía de riesgos de agentes | Hora 2 | Marco (aplica al agente Onyx) |
| **MITRE ATLAS** | Catálogo de técnicas adversarias contra IA/ML | Hora 2 | Marco (aplica al agente Onyx) |
| **PyRIT** | Red-teaming automatizado (Crescendo multi-turno) | Hora 2 | Ataca a Onyx (o al wrapper) |
| **Garak** | Escáner de vulnerabilidades de LLM ("nmap de LLMs") | Hora 2 | Ataca a Onyx (o al wrapper) |
| **FastAPI / uvicorn** | Expone el agente por HTTP para los escáneres | Hora 2-3 | Alternativa a la API de Onyx |
| **Promptfoo** | Evaluaciones automatizadas en CI (anti-regresión) | Hora 3 | Independiente (prueba el sistema) |
| **Node.js** | Solo para Garak/Promptfoo | Hora 2-3 (opcional) | Independiente |
| **Roles SQL / HITL / Router / Pin descriptors** | Las defensas de la Hora 3 | Hora 3 | Soporte (protegen las herramientas que Onyx llama) |

**Conclusión para la diapositiva de cierre:** la gran mayoría de la pila **gira
en torno a Onyx** — es el producto, y todo lo demás (modelo, herramientas MCP,
RAG, base de datos) es lo que lo hace útil y, a la vez, atacable.

---

## 6. Riesgos y pendientes (para no llevarse sorpresas)

- **RAG en Onyx Lite (Lab 2.1):** Lite corre "sin la pila de indexado" pesada.
  Conviene **probar antes** que Onyx cita bien los PDF subidos. Si no, usar Onyx
  Standard en la máquina de demostración, o hacer el Lab 2.1 con el agente CLI.
- **Etiquetas de la UI de Onyx:** cambian entre versiones. Hacer **una pasada de
  prueba completa** antes del taller y ajustar las capturas de la presentación.
- **`docs/guia_completa.html`** (el folleto HTML grande) todavía describe solo la
  Ruta B; si se reparte, conviene regenerarlo con la elección de rutas.
