# Penguins Scatter Plot Matrix (SPLOM) with Vega-Altair `repeat`

## Background
Build a 2x2 scatter plot matrix (SPLOM) of the Palmer Penguins dataset using Vega-Altair's `repeat` operator. Each panel must be a small scatter plot of one beak dimension against one body dimension, with points colored by `Species`. The chart must be saved as a static HTML file that fully renders in a browser.

## Requirements
- Use `data.penguins.url` from `vega_datasets` as the data source (URL-based source; declare types explicitly).
- Render a 2x2 grid of scatter plots produced via the `repeat` operator:
  - `row` repeats over `['Body Mass (g)', 'Flipper Length (mm)']`.
  - `column` repeats over `['Beak Length (mm)', 'Beak Depth (mm)']`.
- Each subplot must:
  - Use `mark_point()`.
  - Encode `x` with `alt.repeat('column')` as a quantitative field, with `scale.zero=False`.
  - Encode `y` with `alt.repeat('row')` as a quantitative field, with `scale.zero=False`.
  - Encode `color` with `Species:N` so points are colored by species.
  - Be sized at `width=180`, `height=180`.
- Save the resulting chart as a single self-contained HTML file using `chart.save(...)`.

## Implementation Hints
- Build a single base `alt.Chart(data.penguins.url).mark_point()` and call `.repeat(row=..., column=...)` on it; the `x`/`y` encodings inside the base chart should use `alt.repeat('column')` / `alt.repeat('row')` so that each panel automatically substitutes the correct field name.
- Because the data source is a URL, the `x`/`y` encodings cannot infer types from a pandas DataFrame: declare them as quantitative via the `type='quantitative'` argument of `alt.X` / `alt.Y`.
- Use `alt.Scale(zero=False)` (or `.scale(zero=False)`) on both axes so that the scatter plots do not pad the axes down to zero.
- The color legend should be shared across all panels (this is the default for `repeat`); do not disable it.
- Use `chart.save('chart.html')` so the output is a self-contained HTML page that loads Vega/Vega-Lite/vega-embed from a CDN.

## Acceptance Criteria
- Project path: /home/user/myproject
- Command: python3 build_chart.py
- The command must produce `/home/user/myproject/chart.html` containing a renderable Vega-Lite specification.
- The embedded Vega-Lite specification must:
  - Define a top-level `repeat` object with:
    - `row` equal to `['Body Mass (g)', 'Flipper Length (mm)']`.
    - `column` equal to `['Beak Length (mm)', 'Beak Depth (mm)']`.
  - Define a `spec` (the repeated subspec) whose `mark` type is `point`.
  - In the repeated subspec encoding:
    - `x.field` must be `{"repeat": "column"}` and `x.type` must be `"quantitative"`.
    - `y.field` must be `{"repeat": "row"}` and `y.type` must be `"quantitative"`.
    - `color.field` must be `"Species"`.
    - `x.scale.zero` and `y.scale.zero` must both be `false`.
  - The repeated subspec must declare `width: 180` and `height: 180`.
- Browser verification: Loading `chart.html` in a browser must render the chart without JavaScript console errors, displaying a 2x2 grid of scatter plots with points colored by species (three distinct colors) and a single shared color legend.

