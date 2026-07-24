# Guía completa: del PC en blanco a la demostración funcionando

Esta guía lleva a cualquier persona, **sin experiencia previa**, desde una
computadora recién encendida hasta ver el agente de *Distribuidora Central*
respondiendo preguntas reales. Está pensada para seguirse paso a paso, sin
saltarse nada.

- **Tiempo estimado:** 30–45 min la primera vez (la mayoría es esperar descargas).
- **Sirve para:** Windows 10/11 y Linux (Ubuntu/Debian). Se indica cada caso.
- **Lo que tendrá al final:** un agente de IA que consulta una base de datos,
  cita documentos de política y actualiza inventario.

> **Cómo leer esta guía.** Cada paso explica *qué* hace y *por qué*, y luego da
> los comandos exactos para copiar y pegar. Si un comando funciona, no imprime
> errores; siga al siguiente. Si algo falla, vaya a **Problemas comunes** al final.

> **Dos rutas, usted elige.** Esta guía monta el agente en su forma **ligera**
> (línea de comandos): funciona en cualquier laptop y es la más estable. Si su
> equipo tiene músculo (Docker + 2 GB de RAM libres) y quiere el efecto completo
> —el agente en una **interfaz web de producto real (Onyx)**—, primero complete
> los Pasos 1 a 6 de aquí (son la base común) y luego siga
> **[ONYX.md](ONYX.md)** en lugar del Paso 7. Los ataques de la Hora 2 y las
> defensas de la Hora 3 son idénticos en ambas rutas.

---

## Antes de empezar: las tres piezas que necesita cada PC

El taller usa tres herramientas. No hay que entenderlas a fondo, solo tenerlas
instaladas:

| Herramienta | Para qué sirve aquí | Obligatoria |
|---|---|---|
| **Python** (3.11 o superior) | Ejecuta el código del agente y los scripts | Sí |
| **Docker** | Levanta la base de datos de la PyME en un contenedor aislado | Sí |
| **Git** | Descarga el código del taller desde GitHub | Sí |
| **Node.js** (20+) | Solo para las herramientas de las Horas 2 y 3 (Garak/Promptfoo) | Opcional |

Además, cada asistente necesita **una llave de API** (se la entrega el tutor) y
conexión a internet.

---

## Paso 1 — Instalar las tres piezas

### En Windows

La forma más rápida es con **winget**, el instalador de paquetes que ya viene en
Windows 10 y 11. Abra **PowerShell** (busque "PowerShell" en el menú Inicio) y
pegue:

```powershell
winget install --id Python.Python.3.12 -e
winget install --id Git.Git -e
winget install --id Docker.DockerDesktop -e
```

Después:

1. **Cierre y vuelva a abrir PowerShell** (para que reconozca lo instalado).
2. **Abra Docker Desktop** desde el menú Inicio y déjelo arrancar hasta que diga
   *"Engine running"*. La primera vez puede pedir reiniciar el PC o activar WSL2;
   acepte. Docker debe estar **corriendo** para el Paso 6.

> Si `winget` no existe en su equipo, descargue e instale a mano desde:
> [python.org/downloads](https://www.python.org/downloads/) (marque la casilla
> **"Add Python to PATH"** durante la instalación),
> [git-scm.com](https://git-scm.com/download/win) y
> [docker.com/products/docker-desktop](https://www.docker.com/products/docker-desktop/).

### En Linux (Ubuntu / Debian)

Abra una terminal y ejecute:

```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip git docker.io docker-compose-v2
# Permite usar Docker sin 'sudo' (cierre sesión y vuelva a entrar tras esto):
sudo usermod -aG docker $USER
```

Cierre la sesión y vuelva a entrar (o reinicie) para que el permiso de Docker
tome efecto.

### Comprobar que todo quedó instalado

Cierre y reabra la terminal, y verifique las versiones. Cada comando debe
imprimir un número, no un error:

```bash
python --version     # en Linux quizá sea: python3 --version
git --version
docker --version
```

---

## Paso 2 — Descargar el taller

`git clone` copia el repositorio completo a su máquina, en una carpeta llamada
`compdes-workshop`:

```bash
git clone https://github.com/DavidMGDev/compdes-workshop.git
cd compdes-workshop
```

A partir de aquí, **todos los comandos se ejecutan dentro de esa carpeta**.

---

## Paso 3 — Instalar las dependencias del taller

El repositorio trae un **instalador guiado** que hace el trabajo pesado: crea un
entorno aislado de Python, instala las librerías y prepara la configuración.

### Windows (PowerShell)

```powershell
powershell -ExecutionPolicy Bypass -File install\setup.ps1
```

### Linux / macOS

```bash
bash install/setup.sh
```

El instalador imprime lo que hace en cada paso. Por dentro:

1. Verifica que Python y Docker estén presentes.
2. Crea un **entorno virtual** (`.venv`): una copia aislada de Python para que
   las librerías del taller no interfieran con el resto de su sistema.
3. Instala las dependencias (esta parte tarda: descarga varios cientos de MB,
   incluida la librería de IA. Es normal que tome unos minutos).
4. Crea su archivo de configuración `.env` a partir de una plantilla.
5. Corre un diagnóstico final.

> **¿Prefiere hacerlo a mano, sin el script?** Todo el proceso manual, comando
> por comando, está en [`SETUP.md`](SETUP.md). Útil si va a **mostrar** el montaje
> en vivo en lugar de automatizarlo.

---

## Paso 4 — Colocar su llave de API

El instalador creó un archivo `.env` con una plantilla. Ábralo con cualquier
editor de texto (Bloc de notas, VS Code, `nano`, etc.) y busque esta línea:

```
OPENAI_API_KEY=PEGUE_SU_LLAVE_AQUI
```

Reemplace `PEGUE_SU_LLAVE_AQUI` por la llave que le dio el tutor (empieza con
`AQ.`). Guarde el archivo. Debe quedar así:

```
OPENAI_API_KEY=AQ.Ab8RN6...el-resto-de-su-llave
```

No cambie nada más: el modelo y los demás valores ya vienen configurados.

> **Cuide su llave.** No la comparta, no la suba a GitHub, no la pegue en
> capturas. El archivo `.env` ya está configurado para que Git nunca lo suba.

---

## Paso 5 — Verificar que todo está listo

Dos comprobaciones. La primera revisa el entorno sin gastar la llave; la segunda
hace **una** llamada real de prueba.

En Windows use `.venv\Scripts\python.exe`; en Linux/macOS use `python` con el
entorno activado (`source .venv/bin/activate`). Los ejemplos usan la forma de
Windows:

```powershell
.venv\Scripts\python.exe install\check_setup.py
.venv\Scripts\python.exe install\check_key.py
```

- `check_setup.py` debe terminar en **"entorno OK"**.
- `check_key.py` debe imprimir **`[OK] FUNCIONA`** y la palabra que respondió el
  modelo. Si lo ve, su llave sirve y puede continuar.

Si `check_key.py` da un error, la tabla de **Problemas comunes** (al final) dice
qué significa cada uno.

---

## Paso 6 — Levantar la base de datos

El agente consulta una base de datos PostgreSQL con datos de la PyME ficticia.
Docker la levanta en un contenedor aislado, ya con los datos cargados. Asegúrese
de que **Docker esté corriendo** (en Windows, que Docker Desktop diga "Engine
running") y ejecute:

```bash
cd target
docker compose up -d
docker compose ps        # debe verse el contenedor como "healthy"
cd ..
```

La primera vez descarga la imagen de PostgreSQL (unos 100 MB). Solo pasa una vez.

---

## Paso 7 — La demostración (Hora 1)

Este es el momento en que se ve el valor. Primero genere los documentos de
política que el agente va a citar, y luego arranque el agente:

```bash
.venv\Scripts\python.exe target\make_policies.py
.venv\Scripts\python.exe target\agent\agent.py
```

(En Linux: `python target/make_policies.py` y `python target/agent/agent.py`,
con el entorno activado.)

El agente queda esperando sus preguntas. Pruebe estas tres, una por una, y
observe qué hace en cada caso:

| Escriba esto | Qué demuestra |
|---|---|
| `¿Cuánto stock tenemos de cemento?` | El agente **consulta la base de datos** y responde con el dato real. |
| `Según nuestra política, ¿qué crédito le doy a un cliente nuevo?` | El agente **cita el documento** de política (RAG). |
| `Sube el stock del SKU-002 a 950.` | El agente **modifica la base de datos** (acción, no solo lectura). |

Para salir del agente, escriba `salir`.

**Qué acaba de ver:** un agente autónomo que, en minutos, razona sobre una
pregunta, decide qué herramienta usar, consulta datos reales y actúa sobre
ellos. Ese es el gancho del taller. En la Hora 2 se descubre que ese mismo poder
—consultar, citar, actuar— es también su superficie de ataque.

---

## Qué sigue: Horas 2 y 3

La Hora 1 construyó el agente. El resto del taller lo pone a prueba:

- **Hora 2 — Romper** ([`../attacks/README.md`](../attacks/README.md)):
  técnicas reales de *red teaming* que abusan de los permisos legítimos del
  agente (inyección vía documentos, envenenamiento de herramientas, jailbreak
  multi-turno, SSRF).
- **Hora 3 — Blindar** ([`../defenses/README.md`](../defenses/README.md)):
  las mitigaciones pragmáticas que una PyME sí puede aplicar, verificando que
  cada ataque de la Hora 2 ahora falla.

Cada carpeta tiene su propio README con los pasos.

---

## Limpieza (al terminar)

Para apagar la base de datos y liberar recursos:

```bash
cd target
docker compose down -v      # apaga el contenedor y borra sus datos
cd ..
```

El entorno virtual (`.venv`) y el código quedan en su carpeta; puede volver a
levantar todo con el Paso 6 cuando quiera.

---

## Problemas comunes

| Síntoma | Causa probable | Solución |
|---|---|---|
| `python: command not found` | Python no quedó en el PATH | En Windows, reinstale marcando "Add Python to PATH". En Linux use `python3`. |
| `check_key.py` → `401 UNAUTHENTICATED` | Llave mal copiada | Cópiela completa, sin espacios ni saltos de línea, en el `.env`. |
| `check_key.py` → `429 ... credits are depleted` | El presupuesto del grupo se agotó | Avise al tutor. No es un error de su código. |
| `check_key.py` → `404 ... model` | El `AGENT_MODEL` del `.env` se modificó | Debe decir `gemini-3.5-flash-lite`. |
| `docker: ... daemon ... not running` | Docker no está encendido | En Windows, abra Docker Desktop y espere a "Engine running". |
| `docker compose` → `permission denied` (Linux) | Falta el permiso del grupo docker | `sudo usermod -aG docker $USER` y vuelva a iniciar sesión. |
| `ModuleNotFoundError` al correr el agente | El entorno no está activo o faltan dependencias | Repita el Paso 3, o active el entorno: `.venv\Scripts\activate` / `source .venv/bin/activate`. |
| `source .venv/bin/activate` → `case ... not inside switch` u otro error raro | Su shell no es *bash* (probablemente **fish** o *csh*) | Use el activador de su shell (`source .venv/bin/activate.fish`), o sáltese la activación y llame al Python del entorno directamente: `.venv/bin/python target/agent/agent.py`. |
| `port 5433 ... in use` | Otro programa ocupa ese puerto | Cambie `5433` por otro puerto en `target/docker-compose.yml` y en `.env`. |
| El agente no usa las herramientas | Modelo o llave con problemas | Confirme con `check_key.py` que la llave responde. |

---

## Referencias rápidas

- [`README.md`](../README.md) — resumen del proyecto.
- [`ONYX.md`](ONYX.md) — **Ruta A:** el agente en Onyx (interfaz web) con sus herramientas MCP.
- [`SETUP.md`](SETUP.md) — instalación **manual**, comando por comando.
- [`PRESUPUESTO.md`](PRESUPUESTO.md) — modelo de IA, precios y control de gasto.
- [`guia_parte1.html`](guia_parte1.html) — guía visual de la Parte 1.
