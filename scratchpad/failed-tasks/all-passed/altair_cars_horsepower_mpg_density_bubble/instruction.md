# 2D Binned Bubble Density Plot of Cars (Horsepower vs MPG) with Vega-Altair

## Background
Build a Vega-Altair visualization that summarizes the classic `cars` dataset as a 2D binned bubble density plot. Each bubble represents a bin in the (Horsepower, Miles_per_Gallon) plane; the bubble size encodes the number of cars falling in that bin, and the bubble color encodes the mean acceleration of those cars. The chart must be exported to a static HTML file that fully renders in a browser.

## Requirements
- Use `data.cars.url` from `vega_datasets` as the data source (URL-based source; declare data types explicitly with shorthand or via channel classes).
- Use `mark_circle()` for the bubbles.
- Bin both axes into at most 10 bins (`maxbins=10`):
  - `x`: `Horsepower` (quantitative).
  - `y`: `Miles_per_Gallon` (quantitative).
- Encode `size` as `count()` of items in each bin.
- Encode `color` as `mean(Acceleration)` using a continuous `viridis` color scheme.
- Set the chart properties: `width=400`, `height=300`, `title="Cars Horsepower vs MPG Density"`.
- Save the resulting chart as a single self-contained HTML file using `chart.save(...)`.

## Implementation Hints
- Build a single `alt.Chart(data.cars.url)` with `mark_circle()` and an `encode(...)` call that maps `x`, `y`, `size`, and `color`.
- For URL-based data, remember to declare types explicitly (e.g. `Horsepower:Q`).
- For 2D binning, use the `bin` channel option on both `alt.X` and `alt.Y` with `maxbins=10` (the resulting Vega-Lite spec will have `bin: {maxbins: 10}` on both axes).
- For the size encoding, use the `count()` aggregate (no field required).
- For the color encoding, use `alt.Color('Acceleration:Q', aggregate='mean')` (or the method-based equivalent) and attach a continuous color scale with `scheme='viridis'`.
- Apply the title and chart dimensions with `.properties(width=400, height=300, title="Cars Horsepower vs MPG Density")`.
- The HTML must contain a renderable Vega-Lite spec (the Altair `chart.save("chart.html")` template embeds the spec in a `var spec = {...};` block consumed by `vegaEmbed`).

## Acceptance Criteria
- Project path: /home/user/myproject
- Command: python3 build_chart.py
- The command must produce `/home/user/myproject/chart.html` containing a renderable Vega-Lite specification.
- The embedded Vega-Lite specification must:
  - Use `mark` of type `circle`.
  - Encode `x` with `field: "Horsepower"` and `bin: {maxbins: 10}`.
  - Encode `y` with `field: "Miles_per_Gallon"` and `bin: {maxbins: 10}`.
  - Encode `size` with `aggregate: "count"`.
  - Encode `color` with `aggregate: "mean"`, `field: "Acceleration"`, and a `scale.scheme` of `"viridis"`.
  - Set top-level `width: 400`, `height: 300`, and `title: "Cars Horsepower vs MPG Density"`.
- Browser verification: Loading `chart.html` in a browser must render the chart without JavaScript errors; the rendered output must visibly contain multiple bubbles of varying sizes arranged in an approximate grid pattern, colored by a viridis ramp, plus a visible color legend showing the viridis ramp.

