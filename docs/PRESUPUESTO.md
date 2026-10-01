# Modelos, precios y control de gasto

## El modelo de facturación cambió: ahora es **prepago**

Google AI Studio / Gemini API funciona con **créditos prepagados**, no con
facturación pospago. Usted **compra crédito por adelantado**; cuando el saldo
llega a $0, **todas** las llaves de los proyectos de esa cuenta dejan de
responder al instante. Google lo documenta hoy como error `402 Payment
Required`; antes era `429 RESOURCE_EXHAUSTED: "prepayment credits are
depleted"`. `install/check_key.py` reconoce los dos.

Esto es una ventaja: el tope es estructural, sin retraso ni cargos sorpresa.

- **Compra mínima:** $5 (al 30-sep-2026; en julio eran $10).
- **Dónde:** [ai.studio](https://ai.studio) → su proyecto → pestaña *Spend* → comprar crédito.
- **Desactive la recarga automática (auto-reload).** Si está activa, el saldo
  se rellena solo y el tope deja de ser un tope.

---

## Un solo modelo, fijo para todo el taller

Todo el proyecto usa **`gemini-3.5-flash-lite`**. No hay elección de modelo:
está fijado en el `.env` y calibrado en todas las guías. Es el modelo 3.5-class
más económico de Google y está afinado para flujos "agénticos" (uso de
herramientas), justo lo que hace este taller.

Precios de referencia de la familia (por 1M de tokens), según el anuncio de
Google de julio 2026. El de `gemini-3.5-flash-lite` se volvió a comprobar en la
página de precios el 30-sep-2026: sigue igual, y la salida incluye los tokens de
"pensamiento".

| Modelo | Entrada | Salida | Nota |
|---|---|---|---|
| **`gemini-3.5-flash-lite`** | **$0.30** | **$2.50** | **El que usamos.** El 3.5-class más barato. |
| `gemini-3.6-flash` | $1.50 | $7.50 | Workhorse, más caro. No lo usamos. |
| `gemini-3.5-flash-cyber` | (no publicado) | (no publicado) | Especializado en ciberseguridad. |

> **Corrección al manual original.** El manual usaba `gemini-3-flash` (Apéndice D
> y Lab 2.5). **Ese identificador no existe** y devuelve `404`. Está reemplazado
> por `gemini-3.5-flash-lite` en todo el proyecto.
>
> Nota: existe un `gemini-2.5-flash-lite` aún más barato ($0.10/$0.40), pero el
> 3.5-lite es el afinado para uso de herramientas y es el que el taller espera.

---

## Reparto de presupuesto de este taller

Las 21 llaves están repartidas en 5 proyectos (límite de 5 proyectos por
cuenta de facturación de Google):

| Proyecto | Llaves | Personas | Tope sugerido |
|---|---|---|---|
| taller-01 … taller-04 | 5 c/u | 5 c/u (grupo) | $5.50 por proyecto |
| taller-05 | 1 | 1 (tutor) | $1.10 |
| **Total** | **21** | **21** | **$23.10** |

**Dos capas de control, ambas en la consola (no hay API/gcloud para esto):**

1. **Crédito prepago total** = $23.10. Es el techo real de todo el gasto.
2. **Tope de gasto por proyecto** (AI Studio → *Spend* → *Monthly spend cap*).
   Reparte el crédito de forma justa entre grupos.

> **Aislamiento dentro de un grupo: no existe.** Los 5 integrantes de un
> proyecto comparten el saldo. Si uno deja un bucle corriendo, agota los $5.50
> del grupo y afecta a los otros cuatro. Es el costo del límite de 5 proyectos.

---

## Cuánto cuesta de verdad (medido)

Medido el **30-sep-2026** corriendo el taller completo con
`gemini-3.5-flash-lite`. El agente anota los tokens de cada llamada
(`USAGE_LOG`) y `tests/costo.py` los pasa a dólares.

| Qué | Llamadas al modelo | Costo |
|---|---|---|
| Hora 1: las tres preguntas de la demo | 5 | $0.0012 |
| Hora 2: los cuatro labs manuales (2.1–2.4), con reintentos | ~17 | $0.006 |
| Hora 3: los mismos ataques contra el agente blindado + demo | ~14 | $0.004 |
| **Una pasada completa de las Horas 1–3** (`tests/`, incluye el wrapper; media de 5) | **39** | **$0.012** |
| Promptfoo (3.7): eval contra el agente blindado y contra el vulnerable | 12 | $0.004 |
| Garak (2.5) acotado: 60 prompts | 60 | $0.014 |
| Garak (2.5) **sin** tope: 768 prompts | 768 | ~$0.18 (extrapolado de los 60) |

**Por asistente:**

- El recorrido guiado, una vez, con Garak acotado: **unos 3 centavos**.
- Un asistente realista, que repite cada lab cinco veces y prueba cosas por su
  cuenta: **10–15 centavos**.
- El caso caro, que además lanza Garak sin tope: **unos 30 centavos**.

Los **$1.10 por asistente** del reparto dejan un margen de más de 3× sobre el
caso caro. Lo que ese margen **no** cubre es un bucle sin freno o un Garak sin
`--probes`: por eso los topes de abajo siguen importando.

> No medido: la Ruta A. Onyx llama a Gemini por su cuenta (con sus propios
> prompts de sistema, más largos) y ese gasto no pasa por `USAGE_LOG`; se ve en
> la pestaña *Spend* de AI Studio.

Para medir su propia sesión:

```bash
USAGE_LOG=mi-sesion.log python target/agent/agent.py     # PowerShell: $env:USAGE_LOG="mi-sesion.log"; python ...
python tests/costo.py mi-sesion.log
```

---

## Consejos para no quemar presupuesto

- **Nunca deje bucles `while` llamando al modelo.** Es la causa #1 de gasto.
- **Garak (Lab 2.5) es la parte más cara.** Acótelo: una sola familia de
  probes (`--probes promptinject`), `--generations 1` y el tope de
  `attacks/2_5_garak_tope.yaml`. Sin eso, Garak puede lanzar miles de prompts.
- **Historiales cortos.** Cada llamada reenvía toda la conversación.
- **No cambie de modelo.** Todo está calibrado a `gemini-3.5-flash-lite`.
