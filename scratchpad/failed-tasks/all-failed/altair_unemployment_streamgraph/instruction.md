# Altair Unemployment Streamgraph with Hover Ruler and Top-Series Annotation

## Background
Build an interactive streamgraph of US unemployment counts across industries using Vega-Altair. The chart must use the standard remote dataset URL `data.unemployment_across_industries.url` (industries reshaped to long form: `date`, `series`, `count`). The streamgraph must reveal the dominant industry at any month via a hover-driven ruler and a text annotation.

## Requirements
- Use Vega-Altair (Python). No external network services are required at runtime beyond reading the remote dataset URL embedded in the spec.
- The output is a single self-contained HTML file (saved by the agent's Python script). The HTML must embed a Vega-Lite specification that fulfills every Acceptance Criterion below.
- The base streamgraph layer must:
  - Use `mark_area` with `interpolate='monotone'`.
  - Encode the X channel as `yearmonth(date):T`.
  - Encode the Y channel as `sum(count):Q` with **center-stack** (i.e., `stack='center'`).
  - Encode the Color channel on `series:N` with a categorical color scheme (use `category20b`).
- A nearest-x hover selection must drive interactive overlays:
  - Use `alt.selection_point` with `on='pointerover'`, `nearest=True`, restricted to the X encoding, and `empty=False`.
  - Overlay a vertical `mark_rule` whose opacity is bound to the hover selection so the ruler appears at the hovered month.
  - Overlay a `mark_text` annotation that displays the **top series for the hovered month** (the series with the largest `count` at that date). Compute the per-date ranking with a `transform_window` that uses the `rank` operation grouped by `date` and sorted by `count` descending, then filter to the rank-1 row before drawing the text. The text annotation should appear only while the hover is active.
- Save the chart as a self-contained HTML file the verifier can open in a browser.

## Implementation Hints
- The remote dataset contains far more than the default Altair row limit; disable that guard once at the top of your script before constructing the chart.
- Center-stack streamgraphs typically hide the Y axis since the baseline is data-dependent.
- For the hover-driven ruler, building the rule layer from the same data source as the area layer keeps the X scale aligned automatically.
- For the top-series annotation, the window-rank transform should be applied to a layer that derives the ranked row per date; a downstream filter on rank == 1 keeps a single label per month so the text does not overplot.
- Compose the layers with `alt.layer(...)`; remember that selection parameters must be attached to at least one layer via `add_params`.
- Encoding-typed selections (`encodings=['x']`) only fire when the pointer is near an actual data point, which is exactly the desired nearest-x behavior for the streamgraph.

## Acceptance Criteria
- Project path: /home/user/myproject
- Command: `python3 solution.py`
- Artifact: The script writes a self-contained HTML file to `/home/user/myproject/out/chart.html`.
- The embedded Vega-Lite spec must include all of the following (the verifier inspects the spec structure):
  - A layer with `mark` of type `area` and `interpolate: "monotone"`.
  - The area layer's Y encoding has `aggregate: "sum"`, `field: "count"`, and `stack: "center"`.
  - The area layer's X encoding uses `timeUnit: "yearmonth"` on `field: "date"` with `type: "temporal"`.
  - The area layer's Color encoding uses `field: "series"` (nominal) and a scale with `scheme: "category20b"`.
  - A param of type `point` with `select.on` containing `"pointerover"`, `select.nearest: true`, `select.encodings` containing `"x"`, and `select.empty: false`.
  - At least one additional layer using `mark` of type `rule` whose opacity (or another channel) is bound to the hover selection (i.e., references the param name in a condition).
  - At least one additional layer using `mark` of type `text` that depends on the rank annotation.
  - A `transform` block on the text/ranking layer that contains a `window` entry with `op: "rank"`, `groupby` including `"date"`, and `sort` referencing `"count"` descending, followed by a `filter` that keeps the top-ranked row.
- The HTML file must render in a Chromium-based browser into a visible streamgraph (vertically centered around zero) with multiple coloured industry bands, and the hover ruler/text overlay must respond to pointer movement.

