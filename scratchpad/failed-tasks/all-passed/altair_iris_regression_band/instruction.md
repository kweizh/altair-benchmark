# Iris Regression + LOESS + Confidence Band with Vega-Altair

## Background
You are building a statistical visualization of the classic Iris dataset using [Vega-Altair](https://altair-viz.github.io/). The goal is a single layered chart that overlays raw measurements with two different trend-line estimators (parametric regression and non-parametric LOESS) and a confidence band, all grouped per species.

The Iris data is available through the `vega_datasets` package as `vega_datasets.data.iris()`. Relevant numeric columns are `petalLength` and `petalWidth`, and the categorical column is `species`.

## Requirements
Produce a single Altair chart composed of **four layers**, all sharing the same x/y encodings (`petalLength` on x, `petalWidth` on y):

1. **Layer A — Raw points.** Use `mark_point` colored by `species`.
2. **Layer B — Parametric regression line per species.** Use `transform_regression('petalLength', 'petalWidth', groupby=['species'])` rendered as `mark_line`.
3. **Layer C — LOESS smoothed line per species.** Use `transform_loess('petalLength', 'petalWidth', groupby=['species'], bandwidth=0.6)` rendered as a **dashed** `mark_line` (use the `strokeDash` mark property).
4. **Layer D — 95% confidence band per species.** Use `mark_errorband` with `extent='ci'`, grouped/colored by `species`, sharing the same x/y fields.

The chart must use a structured `alt.Title` object that includes a main `text` AND a multi-line `subtitle` (a list of two or more strings).

Save the chart to disk as both an interactive HTML file and a Vega-Lite JSON spec.

## Implementation Hints
- Load the data with `vega_datasets.data.iris()` and build a base `alt.Chart`.
- Combine the four layers with `alt.layer(...)` or the `+` operator. Order matters for visual stacking (the band should typically sit underneath the points).
- The LOESS layer needs a dashed stroke; the `mark_line` mark accepts a `strokeDash` argument such as `strokeDash=[4, 4]`.
- Use `alt.Title(text=..., subtitle=[..., ...])` for the multi-line subtitle.
- Persist the spec with `chart.save('chart.json')` and the HTML with `chart.save('chart.html')`.

## Acceptance Criteria
- Project path: /home/user/iris_chart
- Ensure the Python script is actually executed and produces real output artifacts. Do NOT mock Altair output.
- Required output files:
  - `/home/user/iris_chart/chart.py` — the source script that builds and saves the chart.
  - `/home/user/iris_chart/chart.json` — the Vega-Lite JSON spec produced by `chart.save('chart.json')`.
  - `/home/user/iris_chart/chart.html` — the standalone HTML file produced by `chart.save('chart.html')`.
  - `/home/user/iris_chart/output.log` — a log file containing the line `Chart saved: /home/user/iris_chart/chart.html`.
- Spec requirements (inspected via `chart.json`):
  - The top-level spec is a layered chart with at least 4 layers.
  - Exactly one layer contains a `transform` entry with `regression` grouped by `species`.
  - Exactly one layer contains a `transform` entry with `loess` grouped by `species` and `bandwidth = 0.6`.
  - At least one layer uses `mark: "errorband"` (or `mark.type == "errorband"`) with `extent` set to either `"ci"` or `"stderr"`.
  - The collected mark types across all layers include `point`, `line`, and `errorband`.
  - At least one `line` mark has a non-empty `strokeDash` property (used for the LOESS layer).
  - The top-level `title` is a structured object containing both a `text` field and a `subtitle` field, where `subtitle` is an array with at least 2 string entries.
- Browser verification: The generated `chart.html` must successfully render with Vega-Embed and the rendered SVG/Canvas must contain the four layered marks (a scatter of points, a solid regression line, a dashed LOESS line, and a confidence band region).

