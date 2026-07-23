# Modelos, precios y control de gasto

## El modelo de facturación cambió: ahora es **prepago**

Google AI Studio / Gemini API funciona con **créditos prepagados**, no con
facturación pospago. Usted **compra crédito por adelantado**; cuando el saldo
llega a $0, **todas** las llaves del proyecto dejan de responder al instante
(error `429 RESOURCE_EXHAUSTED: "prepayment credits are depleted"`).

Esto es una ventaja: el tope es estructural, sin retraso ni cargos sorpresa.

- **Compra mínima:** $10.
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
Google de julio 2026:

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

## Consejos para no quemar presupuesto

- **Nunca deje bucles `while` llamando al modelo.** Es la causa #1 de gasto.
- **Garak (Lab 2.5) es la parte más cara.** Acótelo: una sola familia de
  probes (`--probes promptinject`) y `--generations 1`. Sin eso, Garak puede
  lanzar miles de prompts.
- **Historiales cortos.** Cada llamada reenvía toda la conversación.
- **No cambie de modelo.** Todo está calibrado a `gemini-3.5-flash-lite`.
