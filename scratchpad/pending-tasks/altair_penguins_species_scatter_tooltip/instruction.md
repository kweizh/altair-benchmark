# Penguins Species Scatter Plot with Vega-Altair

## Background
Build a classic Palmer Penguins exploratory scatter plot with Vega-Altair. The chart visualizes the relationship between flipper length and body mass, while encoding species and sex through color and shape, and provides a multi-field tooltip plus pan/zoom interactivity. The chart must be exported to a static HTML file that renders in a browser.

## Requirements
- Use `vega_datasets.data.penguins.url` as the data source. Because the data is loaded from a URL, you must declare types explicitly using the Altair shorthand (`:Q`, `:N`).
- Build a single `mark_point()` chart with the following encodings:
  - x: `Flipper Length (mm)` as quantitative, with a scale that does not start at zero.
  - y: `Body Mass (g)` as quantitative, with a scale that does not start at zero.
  - color: `Species` as nominal (categorical), so the three penguin species are rendered with distinct colors.
  - shape: `Sex` as nominal, so different sex categories are rendered with distinct shapes. Null/missing sex values must not break the chart.
  - tooltip: a list of 4 fields, in this order: `Species`, `Island`, `Flipper Length (mm)`, `Body Mass (g)`.
- The point mark must be filled (`filled=True`) and rendered at `size=80`.
- Enable pan and zoom on the chart with `.interactive()`.
- Save the resulting chart as a single self-contained HTML file using `chart.save(...)`.

## Implementation Hints
- Use `alt.Chart(data.penguins.url)` and explicit shorthand types because the data comes from a URL (e.g. `'Flipper Length (mm):Q'`).
- Configure the quantitative axes' scales so they don't anchor at zero (this gives a tighter view of the cluster structure).
- Use the method-based encoding syntax (`alt.X(...).scale(...)`, `alt.Y(...).scale(...)`) or the dict-based `alt.Scale(...)` form, whichever you prefer.
- Pass `filled=True` and `size=80` directly to `mark_point(...)`.
- The `tooltip` channel accepts a list of field references; include the exact 4 fields in the requested order.
- `.interactive()` is the idiomatic shortcut for adding a scales-bound interval selection that enables panning and zooming.

## Acceptance Criteria
- Project path: /home/user/myproject
- Command: python3 build_chart.py
- The command must produce `/home/user/myproject/chart.html` containing a renderable Vega-Lite specification.
- The embedded Vega-Lite specification must:
  - Have a top-level `mark` whose `type` is `point`, `filled` is `true`, and `size` is `80`.
  - Encode `x` with the field `Flipper Length (mm)` (quantitative), with a scale where `zero` is `false`.
  - Encode `y` with the field `Body Mass (g)` (quantitative), with a scale where `zero` is `false`.
  - Encode `color` with the field `Species` (nominal).
  - Encode `shape` with the field `Sex` (nominal).
  - Encode `tooltip` as a list of exactly 4 field references: `Species`, `Island`, `Flipper Length (mm)`, `Body Mass (g)`.
  - Declare a selection parameter of type `interval` that is bound to `scales` (the result of `.interactive()`).
- Browser verification: Loading `chart.html` in a browser must render the scatter plot. Points must be visible and use at least 3 distinct colors (one per species) and at least 2 distinct shapes (one per sex category). Hovering over a point must reveal a tooltip whose text contains the species name (e.g. `Adelie`, `Chinstrap`, or `Gentoo`).

