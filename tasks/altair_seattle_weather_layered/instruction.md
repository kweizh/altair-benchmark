# Layered Seattle Weather Chart with Vega-Altair

## Background
Build a richly layered Vega-Altair visualization of the Seattle weather dataset that combines a temperature range area, a mean temperature line, a precipitation bar series on an independent secondary axis, an annotation rule, and a hover-driven tooltip layer. The chart must be exported to a static HTML file that fully renders in a browser.

## Requirements
- Use `data.seattle_weather.url` from `vega_datasets` as the data source (URL-based source; declare types explicitly).
- Compose a single layered chart with at least 5 layers:
  1. A pale-orange `mark_area` showing the daily temperature range (`temp_min` -> `temp_max`) over date.
  2. A `mark_line` showing the daily mean temperature, derived inside the spec via `transform_calculate` from the average of `temp_min` and `temp_max`.
  3. A `mark_bar` showing daily `precipitation` on a secondary y axis, resolved with an independent y scale so it does not share the temperature scale.
  4. A dashed `mark_rule` annotation at y = 0 degrees C, spanning the full x range, with `strokeDash=[4, 4]`.
  5. A nearest-x hover interaction (via `selection_point` with `nearest=True`, `encodings=['x']`, `on='pointerover'`, `empty=False`) that drives a vertical `mark_rule` and a `mark_text` tooltip displaying the date, mean temperature, and precipitation for the hovered date.
- Save the resulting chart as a single self-contained HTML file using `chart.save(...)`.

## Implementation Hints
- Build a shared base `alt.Chart(data.seattle_weather.url)` and create per-layer marks/encodings off it; remember that URL-based data requires explicit type shorthands (e.g. `date:T`, `temp_min:Q`).
- For the area layer, use `y` and `y2` to encode the range between `temp_min` and `temp_max`.
- Use `transform_calculate` to define the mean temperature field used by both the line and the tooltip text.
- Use `resolve_scale(y='independent')` on the layered chart so precipitation bars do not share the temperature scale.
- Use `selection_point(on='pointerover', nearest=True, encodings=['x'], empty=False)` and attach it via `add_params` to the layer(s) that drive the hover state; use `alt.when(...).then(...).otherwise(...)` (or `alt.condition`) to gate the tooltip text/rule opacity on the selection.
- The dashed annotation rule must be drawn across the full x extent at the data value y = 0; remember that `alt.datum(0)` lets you encode a constant data value.
- The HTML must contain rendered chart marks (the Vega-Lite spec embedded in a `<script type="application/json">` block and rendered via `vegaEmbed`).

## Acceptance Criteria
- Project path: /home/user/myproject
- Command: python3 build_chart.py
- The command must produce `/home/user/myproject/chart.html` containing a renderable Vega-Lite specification.
- The embedded Vega-Lite specification must:
  - Be a layered chart with at least 5 layers.
  - Include layer marks of types `area` (with both `y` and `y2` encodings), `line`, `bar`, `rule` (at least one rule with `y=0`), and `text`.
  - Define at least one `transform` of type `calculate` that computes a mean temperature field from `temp_min` and `temp_max`.
  - Set `resolve.scale.y` to `"independent"`.
  - Define exactly one point selection parameter with `nearest: true` and an `on` event containing `pointerover` (or `mouseover`) and `empty: false`.
- Browser verification: Loading `chart.html` in a browser must render the chart (no script errors); the rendered HTML/SVG must include visible `area`, `line`, `bar`, `rule`, and `text` marks.

