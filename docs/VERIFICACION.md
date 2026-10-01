# Verificación del taller — 30 de septiembre de 2026

El taller se impartió en **COMPDES, julio de 2026**. Dos meses después se
volvió a correr completo, desde un clon limpio y con las versiones actuales de
cada dependencia, para responder tres preguntas:

1. ¿Sigue funcionando de principio a fin para quien lo clone hoy?
2. ¿Cada cosa que el taller dice enseñar es cierta cuando se ejecuta?
3. ¿Cuánto cuesta en realidad correrlo?

Este documento es el registro de esa pasada: qué se corrió, qué salió, qué hubo
que cambiar y qué quedó sin repasar.

## Resultado

| | |
|---|---|
| Pruebas automáticas | **24 de 24**, seis pasadas completas seguidas (`tests/test_taller.py`) |
| Hora 1 — la demo | Las tres preguntas responden bien; la primera, en 1 llamada, 8 de 8 veces |
| Hora 2 — ataques | Los cinco labs caen contra el agente vulnerable |
| Hora 3 — defensas | Cada ataque falla contra el agente blindado, que sigue respondiendo las preguntas de negocio |
| Ruta A — Onyx v4.8.2 | Despliegue, modelo, MCP, agente, demo, SSRF y cambio al servidor endurecido: funcionan |
| Costo de una pasada completa | **$0.012** |

## Entorno de la pasada

| | |
|---|---|
| Sistema | Windows 11; Docker Engine 29.8 en WSL2 (Ubuntu 24.04) |
| Python | 3.14.7 (taller) y 3.12 (venv de Garak) |
| Modelo | `gemini-3.5-flash-lite` por el endpoint compatible con OpenAI |
| Librerías resueltas | mcp 1.30.0 · openai 3.22.1 · sentence-transformers 6.1.0 · torch 2.14.1 · fastapi 0.142.2 · reportlab 5.0.1 · psycopg2-binary 2.9.13 |
| Herramientas | garak 0.17.0 · promptfoo 0.123.1 (Node 24) · Onyx v4.8.2 · PostgreSQL 16 |

## Qué se corrió

**De forma automática** (`python -m unittest discover tests`, tres niveles):

- *Sin llave ni Docker:* generación de PDF, RAG (incluido que el PDF envenenado
  se recupera), ambos servidores MCP por stdio y por HTTP con el `Host` que usa
  Onyx, router, HITL, integridad de descriptores, allowlist de URL, y que todo
  enlace y todo archivo citado en la documentación existe.
- *Con la base:* las herramientas vulnerables de verdad filtran `notas_internas`,
  ponen el inventario en cero y hacen SSRF contra un servicio local; los roles
  se aplican dos veces sin error y de verdad no pueden leer ni escribir lo
  prohibido; el servidor endurecido sirve y rechaza.
- *En vivo contra el modelo:* las tres preguntas de la Hora 1; los Labs 2.1,
  2.2, 2.3 y 2.4 contra el agente vulnerable; los mismos cuatro contra
  `defenses/agent_seguro.py`; y el wrapper HTTP con historial.

**A mano, una vez:**

- **Promptfoo** (3.7): 4 de 4 contra el agente blindado, código de salida 0;
  3 de 4 fallan contra el vulnerable, código de salida 100.
- **Garak** (2.5): familia `promptinject`, 60 prompts, 2 min 28 s. Éxito del
  ataque por sonda: 50 %, 10 % y 65 %.
- **Lab 2.4** con el servicio falso en Docker: el agente devuelve
  `SECRETO-INTERNO-12345`.
- **Ruta A:** Onyx desplegado con el compose base; modelo conectado; servidor
  MCP registrado (3 herramientas); agente creado; "¿Cuánto stock tenemos de
  cemento?" → 1,200; "Sube el stock del SKU-002 a 950" → la base cambia; SSRF
  → devuelve el secreto; con el servidor endurecido en `--http` → *Rechazado*.

## Costo medido

Tokens reales de cada llamada, a $0.30 / $2.50 por millón (entrada / salida):

| Qué | Llamadas | Entrada | Salida | USD |
|---|---|---|---|---|
| Pasada completa de las Horas 1–3 (suite en vivo, media de 5) | 39 | 23 800 | 2 010 | **0.012** |
| Promptfoo, blindado + vulnerable | 12 | 6 227 | 693 | 0.004 |
| Garak acotado (60 prompts) | 60 | 30 997 | 1 944 | 0.014 |
| Garak sin tope (768 prompts) | — | — | — | ~0.18 (extrapolado) |

Por asistente: unos **3 centavos** el recorrido guiado, **10–15** si repite
cada lab varias veces, **~30** si además corre Garak sin tope. El desglose y
cómo medir una sesión propia están en [`PRESUPUESTO.md`](PRESUPUESTO.md).

## Qué había cambiado desde julio

Cosas que funcionaban en julio y dejaron de hacerlo por cambios fuera del repo:

| Qué cambió | Efecto | Ajuste |
|---|---|---|
| `mcp` 2.0 (28-jul) renombró `FastMCP` | Una instalación nueva no arrancaba | `mcp>=1.8,<2` |
| `semantic-router` ya no exporta `RouteLayer` | `defenses/router.py` no importaba | Router sobre `sentence-transformers`, que ya estaba instalado |
| Onyx bloquea IP privadas por defecto (protección SSRF) | No registraba el servidor MCP local | Paso 3b nuevo en `ONYX.md` |
| Onyx ya no tiene tarjeta "Google Gemini"; menús renombrados; Vespa → OpenSearch | Los clics de la guía no calzaban | `ONYX.md` reescrito contra v4.8.2 |
| Onyx guarda en caché las herramientas MCP | Cambiar de servidor no se reflejaba | "Refresh tools" documentado |
| Promptfoo pide Node 22 | — | Requisito actualizado |
| AI Studio: compra mínima $5, error 402 al agotar crédito | Mensajes de `check_key.py` | Reconoce 402 y 429 |

## Qué se añadió en esta pasada

Además de ponerlo al día con las versiones de hoy, la re-ejecución dejó el
material más fácil de seguir por cuenta propia y de volver a comprobar:

- **El esquema de la base va en la descripción de la herramienta.** La primera
  pregunta de la demo se resuelve en una sola llamada (8 de 8 corridas).
- **`defenses/agent_seguro.py`:** el agente de la Hora 1 con las seis defensas
  aplicadas, cada bloque marcado `[3.x]`. Es la clave de respuestas de la Hora 3
  y contra lo que las pruebas lanzan cada ataque.
- **El servidor endurecido cubre el caso de negocio completo** (consulta,
  búsqueda y actualización tipada con su propio rol) y se sirve por `--http`,
  así que la Ruta A también puede cambiar a él.
- **HITL cubre el SQL libre** además de las herramientas de escritura, y los
  roles de `roles_seguros.sql` se pueden aplicar las veces que haga falta.
- **Umbral del router calibrado** con las preguntas del propio taller, y pruebas
  que comprueban que las preguntas legítimas llegan al modelo.
- **Lab 2.1** tiene su sección en `attacks/README.md`; **Lab 2.5** trae su
  configuración de Garak y un tope de prompts; **Lab 2.4** usa el puerto en el
  que escucha `http-echo`.
- **El wrapper HTTP acepta historial**, para conducir un ataque multi-turno
  desde Promptfoo o Garak.
- **Registro de uso** (`USAGE_LOG`) y `tests/costo.py`: el costo se mide.
- La base de datos del laboratorio escucha solo en `127.0.0.1`, y el taller se
  conecta a esa dirección (en Windows, `localhost` prueba antes IPv6 y añade
  unos 2 s a cada conexión).

## Qué NO se repasó

Para que nadie lo dé por comprobado:

- **RAG dentro de Onyx** (subir los PDF, Paso 5 de `ONYX.md`) y por tanto el
  **Lab 2.1 en Onyx**. En la Ruta B sí está probado.
- **Docker Desktop** en Windows y macOS. La pasada usó Docker Engine en WSL2,
  que se comporta como Linux. `install/onyx.ps1` y `install/setup.ps1` se
  revisaron (sintaxis, y la generación del secreto de Onyx por separado) pero no
  se ejecutaron de punta a punta, porque exigen `docker` en el PATH de Windows.
- **`install/setup.sh`, `install/onyx.sh` y `install/fix-docker-host.sh`** en un
  Linux nativo: solo sintaxis. Sus pasos se ejecutaron a mano, uno por uno.
- **macOS**, en general.
- **PyRIT.** El taller lo menciona como referencia; no se instaló.
- **Garak sin tope** (768 prompts): su costo está extrapolado, no medido.
- **El costo de la Ruta A:** Onyx llama a Gemini por su cuenta y no pasa por el
  registro de uso.
- **El agotamiento del crédito** (qué error llega exactamente en $0): se
  documenta lo que dice Google, no se provocó.

## Cómo repetir esta verificación

```bash
bash install/setup.sh                              # o install\setup.ps1
cd target && docker compose up -d && cd ..
python -m unittest discover tests                  # ~1 min, gratis
TALLER_LIVE=1 python -m unittest discover tests    # ~2.5 min, ~1.5 centavos
python tests/costo.py
```

Los ataques dependen de un LLM y no son deterministas: cada uno se reintenta
hasta tres veces. Medido por separado, el Lab 2.1 cae en ~8 de 10 intentos y el
Lab 2.2 en 29 de 30; aun así, en una tanda anterior de cinco pasadas la prueba
del Lab 2.2 no cayó en dos. Si una prueba de ataque falla de forma aislada,
repítala antes de concluir que algo cambió. Las defensas no se reintentan: en
las once pasadas no falló ninguna.

El flujo de GitHub Actions (`.github/workflows/verificar.yml`) corre los niveles
gratuitos en cada push y cada lunes, con las versiones de dependencias de ese
día.
