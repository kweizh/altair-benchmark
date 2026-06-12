# Hover-Driven Nearest-Point Highlight Scatter with Vega-Altair

## Background
Build an interactive Vega-Altair scatter chart of the classic Cars dataset that uses a pointer-driven point selection to highlight the nearest point and reveal its car name on hover. The chart must be exported to a static HTML file that renders in a browser, with the hover interaction visibly working.

## Requirements
- Use `data.cars.url` from `vega_datasets` as the data source (URL-based source; declare types explicitly).
- Build a single layered chart that combines a point layer and a text label layer:
  - Base scatter: `x=Horsepower:Q` and `y=Miles_per_Gallon:Q`, with both axes' scales configured so `zero=False`.
  - Hover selection: use `selection_point` configured for `on='pointerover'`, `nearest=True`, and `empty=False`, attached to the chart via `add_params`.
  - Point layer (`mark_point`): the `color` channel is conditional on the hover selection. When a point is hovered, it is colored by `Origin:N`; otherwise it falls back to the value `'lightgray'`.
  - Text label layer (`mark_text` with `dy=-10`): renders the `Name:N` field. The `opacity` channel is conditional on the hover selection: opacity is `1` when the point is hovered and `0` otherwise.
- Set chart `width=600` and `height=400`.
- Save the resulting chart as a single self-contained HTML file using `chart.save(...)`.

## Implementation Hints
- Build a shared base `alt.Chart(data.cars.url)` and create per-layer marks/encodings off it; URL-based data requires explicit type shorthands (e.g. `Horsepower:Q`, `Origin:N`, `Name:N`).
- Configure `zero=False` on each axis with the `.scale(zero=False)` method on `alt.X` / `alt.Y`.
- Use `alt.selection_point(on='pointerover', nearest=True, empty=False)` and attach it via `add_params` to the point layer that drives the hover state.
- Use `alt.condition(hover, ...)` (or `alt.when(hover).then(...).otherwise(...)`) to gate the color of points and the opacity of the text label on the hover selection.
- The text label layer should render the car `Name` as the text and be offset vertically with `dy=-10` so it appears above the hovered point.
- The HTML must contain a renderable Vega-Lite spec embedded in the Altair-generated template and rendered via `vegaEmbed`.

## Acceptance Criteria
- Project path: /home/user/myproject
- Command: python3 build_chart.py
- The command must produce `/home/user/myproject/chart.html` containing a renderable Vega-Lite specification.
- The embedded Vega-Lite specification must:
  - Be a layered chart whose top-level `layer` array has at least 2 entries.
  - Include a `point` layer and a `text` layer.
  - The point layer's `mark.type` must be `point`; its `encoding.color` must use a `condition` referencing the hover selection parameter (then field `Origin`) with a fallback `value` of `lightgray`.
  - The text layer's `mark.type` must be `text` with `mark.dy == -10`; its `encoding.text.field` must be `Name`; its `encoding.opacity` must use a `condition` referencing the hover selection parameter that resolves to `1` when active and `0` otherwise.
  - Both `x` and `y` encoding scales must have `zero: false`.
  - The spec's top-level `width` must be `600` and `height` must be `400`.
  - Declare exactly one point selection parameter with `nearest: true`, `empty: false`, and an `on` event string containing `pointerover` (or `mouseover`).
- Browser verification: Loading `chart.html` in a browser must render the chart without JavaScript console errors. Unhovered points must appear in light gray. Moving the pointer over a point area must cause the nearest point to change color (matching its `Origin` category) AND a text label (the car's `Name`) must appear next to it.

