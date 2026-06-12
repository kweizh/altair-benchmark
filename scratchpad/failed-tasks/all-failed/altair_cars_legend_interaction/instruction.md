# Shared Legend-Driven Cars Dashboard with Vega-Altair

## Background
Vega-Altair is a declarative statistical visualization library for Python that compiles to Vega-Lite. In this task you will build an interactive multi-view dashboard on the classic `cars` dataset (available as `vega_datasets.data.cars`). The dashboard is driven by a SINGLE shared legend-bound selection over `Origin` so that clicking an entry in the `Origin` legend simultaneously highlights/dims the matching marks in three different charts.

## Requirements
Produce a single Python entry-point at `/home/user/myproject/solution.py` that, when executed, builds the chart and writes a Vega-embed HTML file to `/home/user/myproject/chart.html`.

The rendered chart must contain exactly three sub-views composed in the layout `(A | B) & C`:

- **View A — Scatter (`mark_point` or `mark_circle`)**
  - x: `Horsepower` (quantitative)
  - y: `Miles_per_Gallon` (quantitative)
  - color: `Origin` (nominal)
- **View B — Stacked bar chart (`mark_bar`)**
  - x: `Cylinders` as an ordinal axis (`Cylinders:O`)
  - y: `count()` aggregate (quantitative)
  - color: `Origin` (nominal)
  - The bars MUST be stacked along the y axis by `Origin` (one stacked bar per Cylinders value). Do NOT make this a side-by-side / grouped bar chart, i.e. do not use an `xOffset` encoding.
- **View C — Histogram (`mark_bar`)**
  - x: `Acceleration` (quantitative), binned
  - y: `count()` aggregate (quantitative)
  - color: `Origin` (nominal)

## Shared Legend Selection (the central requirement)
Define ONE `selection_point` parameter projected over `fields=['Origin']` and bound to the `Origin` color legend with `bind='legend'`. This single shared selection MUST drive opacity in all three sub-views:

- When NOTHING is selected (initial state), every mark must be fully opaque (opacity ≈ 1).
- When the user clicks an `Origin` legend entry, marks belonging to that origin in ALL THREE charts must remain fully opaque (≈ 1), and marks belonging to the OTHER origins must be dimmed (≈ 0.15).
- Clicking the same legend entry again (or clicking the background) must clear the selection and restore full opacity everywhere.

This behavior MUST be implemented with `alt.condition(selection, alt.value(1), alt.value(0.15))` (or the equivalent `alt.when(...).then(...).otherwise(...)` API) bound to the `opacity` channel on each of the three views. All three views MUST reference the SAME parameter — do not create a second selection for the bar chart or the histogram.

Compose the three views as `(A | B) & C` using Altair's `|` and `&` operators, so the top-level Vega-Lite spec is a `vconcat` whose first row is an `hconcat` of A and B and whose second row is C.

## Implementation Hints
- Use `vega_datasets.data.cars` (or `data.cars.url`) as the input data.
- Use the Altair 5+ `selection_point(fields=[...], bind='legend')` API and attach the selection to the composed dashboard with `add_params(...)`. A single shared parameter attached at the top level is reused by every subview that references it.
- Use `alt.condition(...)` (or `alt.when(...).then(...).otherwise(...)`) on the `opacity` channel of each subview — pass `alt.value(1)` and `alt.value(0.15)`.
- For the histogram, use Altair's binning API (e.g. `alt.X('Acceleration:Q').bin()` or `alt.X('Acceleration', bin=True)`) together with `y='count()'`.
- For the stacked bar chart, encode the categorical color with `Origin:N` and let Vega-Lite stack the bars by default (do NOT add an `xOffset` encoding, which would produce a grouped/side-by-side bar chart instead of a stacked one).
- Save the chart with `chart.save('/home/user/myproject/chart.html')` so the resulting HTML embeds the full Vega-Lite spec.
- Avoid hard-coding visual styling such as widths, fonts, color palettes, or titles — the verifier intentionally ignores these.

## Acceptance Criteria
Project path: /home/user/myproject
Command: python solution.py
Artifact: /home/user/myproject/chart.html

The verifier extracts the embedded Vega-Lite JSON spec from `chart.html` and checks:

- The top-level spec uses `vconcat` containing exactly 2 entries; the first entry uses `hconcat` containing exactly 2 entries. (Layout = `(A | B) & C`.)
- The spec declares exactly one shared point-selection parameter (visible either at the top-level `params` of the composed spec, or replicated identically across the sub-views) whose `select.type == 'point'`, whose `select.fields` contains `'Origin'`, and whose `select.bind == 'legend'`. Record its parameter name as `legend_param`.
- View A (first entry inside `hconcat`):
  - mark is `point` or `circle`.
  - `encoding.x.field == 'Horsepower'`, `encoding.y.field == 'Miles_per_Gallon'`, `encoding.color.field == 'Origin'`.
  - `encoding.opacity` is a conditional expression that references `legend_param` and resolves to a high opacity value (≈ 1) when selected and a low opacity value (≤ 0.5) otherwise.
- View B (second entry inside `hconcat`):
  - mark is `bar`.
  - `encoding.x.field == 'Cylinders'` with ordinal type (`type == 'ordinal'`), `encoding.y.aggregate == 'count'`, `encoding.color.field == 'Origin'`.
  - The bar chart MUST be stacked, NOT grouped: the spec must NOT contain an `encoding.xOffset` channel. Stacking may be expressed implicitly by Vega-Lite defaults or explicitly via `stack`; either is accepted as long as no `xOffset` channel is present.
  - `encoding.opacity` is a conditional expression referencing the same `legend_param` with the same selected ≈ 1 / unselected ≤ 0.5 semantics.
- View C (second entry of the top-level `vconcat`):
  - mark is `bar`.
  - `encoding.x.field == 'Acceleration'` and `encoding.x.bin` is truthy (either `true` or an object).
  - `encoding.y.aggregate == 'count'`.
  - `encoding.color.field == 'Origin'`.
  - `encoding.opacity` is a conditional expression referencing the same `legend_param` with the same selected ≈ 1 / unselected ≤ 0.5 semantics.

In addition, a browser verification step opens `chart.html` through a local HTTP server, waits for the Vega-embed runtime to render, and confirms that three sub-views are visible, the `Origin` legend is clickable, and clicking a legend entry simultaneously highlights the matching marks across all three views (dimming the other origins).

