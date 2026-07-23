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

## Modelos disponibles (precios reales, por 1M de tokens)

| Modelo | Entrada | Salida | Uso recomendado |
|---|---|---|---|
| `gemini-2.5-flash-lite` | $0.10 | $0.40 | **Por defecto.** Barato, con *function calling*. |
| `gemini-2.5-flash` | $0.30 | $2.50 | Más capaz si un lab lo necesita. |
| `gemini-3.5-flash` | $1.50 | $9.00 | El más caro. Solo si hace falta razonamiento fuerte. |

> **Corrección al manual original.** El manual usaba `gemini-3-flash` (Apéndice D
> y Lab 2.5). **Ese identificador no existe** y devuelve `404`. Si necesita la
> familia 3, el id real es `gemini-3-flash-preview`. Para todo el taller,
> `gemini-2.5-flash-lite` es suficiente y el más barato.

Cambiar de modelo = una línea en `.env`:
```
AGENT_MODEL=gemini-2.5-flash-lite
```

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
- **Pruebe con `flash-lite`** y suba de modelo solo si el flujo ya funciona.
