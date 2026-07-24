# Ruta Onyx — el agente de la PyME con una interfaz real

Esta es la **ruta completa** del taller: en vez de un agente de línea de
comandos, usted ejecuta **Onyx**, una plataforma de IA de código abierto
(antes llamada *Danswer*, MIT). Onyx le da una interfaz de chat web real, hace
RAG sobre sus documentos y —lo importante para el taller— llama a **sus
herramientas MCP**. Es el mismo agente vulnerable, pero con la cara de un
producto empresarial de verdad.

> **¿Es esta su ruta?** El taller tiene **dos caminos, usted elige**:
>
> | | Ruta A — **Onyx** (esta guía) | Ruta B — **CLI ligero** |
> |---|---|---|
> | Experiencia | Interfaz web real, "producto" | Terminal, mínima |
> | Requisitos | Docker + **~16 GB RAM libres** para Onyx Standard | Solo Python + Docker |
> | Montaje | ~20–30 min extra (stack de Onyx) | Ya está en [`GUIA_COMPLETA.md`](GUIA_COMPLETA.md) |
> | Cuándo | Su laptop tiene músculo y quiere el efecto completo | Laptop justa, o quiere lo más simple y estable |
>
> Ambas usan **la misma base de datos y las mismas herramientas MCP**, así que
> **todos los ataques de la Hora 2 y las defensas de la Hora 3 funcionan igual**
> en las dos. Si Onyx no arranca en su equipo, pásese a la Ruta B sin perder nada.

> **Nota de honestidad.** Onyx evoluciona rápido: los nombres exactos de botones
> y menús pueden variar entre versiones. Esta guía se basa en la documentación
> oficial vigente. **Haga una pasada de prueba usted mismo antes del taller** —
> sobre todo el Paso 5 (RAG en Onyx Standard), que es el único punto con margen de
> duda. Si algo no calza, la lógica es la misma; ajuste el clic.

---

## Cómo encaja todo

```
   Navegador  ─────────►  Onyx Standard  (localhost:3000)
   del asistente          • Chat + Asistente
                          • RAG sobre los PDF de política
                          • LLM = su llave de Gemini
                                │
                    Acción MCP  │  http://host.docker.internal:9000/mcp
                                ▼
                   inventory_mcp_server.py --http     ← SUS herramientas
                          (consultar_inventario / actualizar_stock / validar_enlace)
                                │
                                ▼
                   PostgreSQL (target/)  ← los "datos joya" de la PyME
```

Dos procesos corren en **su** máquina (la base de datos y el servidor MCP) y
Onyx corre en contenedores. Onyx alcanza su servidor MCP a través de
`host.docker.internal` (el nombre con que un contenedor ve a la máquina que lo
hospeda).

---

## Requisitos

- Todo lo de la [guía base](GUIA_COMPLETA.md) (Python, Docker, Git) **ya montado**:
  el repo clonado, el entorno `.venv` creado y su llave en `.env`.
- **Docker corriendo** con **~16 GB de RAM libres** para Onyx Standard (la pila
  completa: Vespa + Redis + model-servers, necesaria para el RAG real). Si su
  laptop no los tiene, use la **Ruta B (CLI)**, que hace RAG local sin Onyx.
- Espacio en disco: ~15 GB (las imágenes de Onyx Standard pesan).

> **Consejo de logística.** Descargue las imágenes de Onyx **antes** del taller
> (Paso 2), no el día del evento con 21 personas compitiendo por el wifi.

---

## Atajo: un solo script (opcional)

Los Pasos 1 a 5 (levantar la base de datos, el servidor MCP, desplegar Onyx
Standard y generar los PDF) están automatizados. Deja además un `onyx-config.txt` con los
valores exactos para pegar en Onyx:

```powershell
powershell -ExecutionPolicy Bypass -File install\onyx.ps1   # Windows
```
```bash
bash install/onyx.sh                                          # Linux / macOS
```

Requiere haber corrido antes el instalador base (`install/setup.*`, que crea el
`.venv`). El script termina dejando **el servidor MCP corriendo en esa ventana**
—no la cierre— y abre `http://localhost:3000`. Luego siga desde el **Paso 3**
(conectar el modelo) usando `onyx-config.txt`.

> **¿Prefiere verlo a mano?** Los pasos siguientes son exactamente lo que hace el
> script, uno por uno. Útil para mostrarlo en vivo.

---

## Paso 1 — Levante la base de datos y el servidor MCP

Estos dos procesos son el "backend" que Onyx va a consumir. Ábralos en dos
terminales y **déjelos corriendo**.

**Terminal 1 — la base de datos** (igual que en la ruta CLI):

```bash
cd target
docker compose up -d
docker compose ps        # debe verse "healthy"
cd ..
```

**Terminal 2 — el servidor MCP en modo HTTP** (la novedad de esta ruta). Onyx
corre en contenedores y **no puede hablar por stdio**, así que exponemos las
herramientas por HTTP:

```powershell
# Windows
.venv\Scripts\python.exe target\mcp\inventory_mcp_server.py --http
```
```bash
# Linux / macOS
.venv/bin/python target/mcp/inventory_mcp_server.py --http
```

Debe imprimir:

```
[MCP] HTTP en http://0.0.0.0:9000/mcp (Onyx: http://host.docker.internal:9000/mcp)
```

Déjelo abierto. Ese `http://host.docker.internal:9000/mcp` es la dirección que
le dará a Onyx en el Paso 4.

---

## Paso 2 — Despliegue Onyx Standard

Onyx es un proyecto **aparte**; se clona y se levanta con su propio Docker
Compose. Usamos el modo **Standard** (con base de datos vectorial Vespa, Redis y
model-servers): es el que hace **RAG de verdad** sobre los PDF y sostiene el
flujo de herramientas. Pide **~16 GB de RAM**; si su laptop no los tiene, pásese
a la **Ruta B (CLI)**.

> **¿Por qué ya no Lite?** Lite quita la pila de indexado, y con ella el RAG cita
> mal y el agente queda a medias. Para el efecto completo (RAG + herramientas MCP)
> se necesita Standard.

```bash
# En una carpeta FUERA del repo del taller (Onyx es independiente):
git clone --depth 1 https://github.com/onyx-dot-app/onyx.git
cd onyx/deployment/docker_compose
cp env.template .env          # configuración por defecto; no hay que editar nada para el taller
```

Arranque en modo Standard. La forma guiada (sin `--lite`):

```bash
./install.sh
```

O, de forma explícita (útil para **mostrar** qué hace por dentro) — solo el
compose base, **sin** el overlay de Lite:

```bash
docker compose -f docker-compose.yml up -d
```

> **Windows:** `install.sh` es un script de shell; use el comando explícito de
> `docker compose` de arriba desde Git Bash o WSL, o desde PowerShell (Docker
> Desktop trae `docker compose`).

La primera vez descarga varios GB. Standard tarda **varios minutos** en indexar y
quedar listo. Cuando termine, abra **http://localhost:3000**. Onyx le pedirá
**crear una cuenta de administrador** (correo y contraseña locales, solo para su
instancia). Créela y entre.

Para **apagar** Onyx al terminar: `./install.sh --shutdown` (o
`docker compose -f docker-compose.yml down`).

---

## Paso 3 — Conecte su llave de Gemini

Onyx necesita un modelo. Le damos el mismo del taller.

1. Clic en su perfil → **Admin Panel**.
2. En el menú, **LLM** (proveedores de modelo).
3. Añada un proveedor. **Use el Gemini NATIVO**, no el compatible con OpenAI:
   - **Gemini nativo (recomendado):** elija *Google Gemini* (si no aparece,
     *Custom* con **Provider Name = `gemini`**), pegue su llave (`AQ...`) y ponga
     el modelo `gemini-3.5-flash-lite` (sin prefijo; Onyx antepone `gemini/`).
4. Guarde y márquelo como modelo por defecto.

> **⚠ Importante para las herramientas (Paso 4).** El endpoint **compatible con
> OpenAI** de Google (`.../v1beta/openai/`) sirve para chatear, pero traduce mal
> las *tool-calls*: cuando el agente intenta llamar a una herramienta MCP, da
> error. Para que las herramientas funcionen, **el proveedor del modelo en Onyx
> debe ser el Gemini nativo** (arriba). El endpoint OpenAI-compatible queda para
> la **Ruta B (CLI)**, donde no hay este problema.

---

## Paso 4 — Registre sus herramientas MCP (esto es el corazón)

Aquí es donde Onyx deja de ser un chat bonito y se vuelve un **agente con
poder** —el mismo poder que atacaremos en la Hora 2.

1. **Admin Panel → Actions → MCP Actions** → **Add MCP Server**.
2. Complete:
   - **Server Name:** `Distribuidora Central`
   - **MCP Server URL:** `http://host.docker.internal:9000/mcp`
   - **Auth:** *No Auth* (es local, sin token).
3. **Connect.** Onyx debe listar tres herramientas:
   `consultar_inventario`, `actualizar_stock`, `validar_enlace_proveedor`.
4. **Selecciónelas** para que el agente pueda usarlas.

> **Linux — si `host.docker.internal` no resuelve:** en Linux ese nombre a veces
> no existe dentro del contenedor. Use la IP del *bridge* de Docker en su lugar:
> `http://172.17.0.1:9000/mcp`. (En Docker Desktop de Windows/macOS,
> `host.docker.internal` funciona sin más.)

Ahora dígale al **Asistente por defecto** (o cree uno nuevo, "Asesor de
Distribuidora") que puede usar estas acciones, y déle una instrucción de sistema
como la del agente CLI:

```
Usted es el asistente de Distribuidora Central. Ayuda con inventario, precios y
clientes. Use las herramientas disponibles cuando sea necesario. Conteste de
forma profesional y en español.
```

---

## Paso 5 — Cargue los documentos de política (RAG)

Para que el agente cite políticas (y para el Lab 2.1), Onyx necesita los PDF.

```powershell
.venv\Scripts\python.exe target\make_policies.py     # Windows
```
```bash
.venv/bin/python target/make_policies.py             # Linux/macOS
```

Eso genera los PDF en `target/policies/`. En Onyx, súbalos como **documentos**
(a un *connector* de archivos o directamente al asistente, según su versión) para
que el agente los recupere.

> **RAG en Standard.** Con Onyx **Standard** (el que despliega esta guía) la pila
> de indexado (Vespa) está completa, así que el recuperador RAG cita bien los
> PDF. Tras subirlos, deles **un par de minutos** para que el indexador los
> procese antes de preguntarles. Si su laptop no aguanta Standard y debe caer a
> Lite, el RAG queda flojo: en ese caso haga el **Lab 2.1 (PDF envenenado)** con
> el agente CLI de la Ruta B, que hace RAG local garantizado.

---

## Paso 6 — La demostración (Hora 1), ahora en Onyx

Abra el chat en `localhost:3000` y haga las tres preguntas de siempre. El efecto
es más fuerte porque se ve en una interfaz de producto:

| Escriba esto | Qué demuestra |
|---|---|
| `¿Cuánto stock tenemos de cemento?` | Onyx llama a `consultar_inventario` y responde con el dato real. |
| `Según nuestra política, ¿qué crédito le doy a un cliente nuevo?` | Onyx **cita el PDF** de política (RAG). |
| `Sube el stock del SKU-002 a 950.` | Onyx **modifica la base de datos** vía `actualizar_stock`. |

Ese es el gancho: un agente empresarial real, con UI, en minutos. En la Hora 2
descubrimos que ese mismo poder es su superficie de ataque.

---

## Cómo caen los ataques de la Hora 2 en Onyx

Todos los labs de [`../attacks/README.md`](../attacks/README.md) aplican; solo
cambia *dónde* se escribe:

| Lab | En Onyx |
|---|---|
| **2.1** Inyección vía RAG | Suba el **PDF envenenado** como documento y haga una pregunta inocente en el chat. *(Standard indexa bien; deje unos minutos tras subir. Ver Paso 5.)* |
| **2.2** Tool poisoning | Edite la *docstring* de `consultar_inventario` en el servidor MCP, **reinicie el servidor MCP** (Terminal 2). Onyx relee la descripción envenenada. |
| **2.3** Crescendo | Conduzca la secuencia multi-turno directamente en el chat de Onyx. |
| **2.4** SSRF | Pídale al chat que "valide" `http://169.254.169.254/...`; dispara su herramienta `validar_enlace_proveedor`. |
| **2.5** Garak/PyRIT | Automatizado: apunte la herramienta al endpoint HTTP del agente (`http_wrapper.py`) o a la API de chat de Onyx. |

En la Hora 3, cuando cambie al servidor MCP endurecido
([`../defenses/inventory_mcp_server_seguro.py`](../defenses/inventory_mcp_server_seguro.py)),
solo relance ese servidor en `--http` y **repita el ataque en Onyx**: ahora falla.

---

## Limpieza

```bash
# Apague Onyx
cd onyx/deployment/docker_compose && ./install.sh --shutdown

# Detenga el servidor MCP (Terminal 2): Ctrl+C

# Apague la base de datos del taller
cd target && docker compose down -v
```

---

## Referencias

- [`GUIA_COMPLETA.md`](GUIA_COMPLETA.md) — la ruta base (Ruta B, CLI) y el montaje común.
- [`../attacks/README.md`](../attacks/README.md) — los labs de la Hora 2.
- [`../defenses/README.md`](../defenses/README.md) — las defensas de la Hora 3.
- [Documentación oficial de Onyx](https://docs.onyx.app) — despliegue y acciones MCP.
