# Focus + Context S&P 500 Brush Range with Vega-Altair

## Background
Build a classic overview + detail (focus + context) Vega-Altair visualization of the S&P 500 dataset. A small overview area chart at the bottom hosts an interval brush over the time axis, and a larger detail area chart at the top dynamically rescales its x-axis to the brushed time window. The chart must be exported to a static HTML file that fully renders in a browser, including the interactive linked brushing behavior.

## Requirements
- Use `data.sp500.url` from `vega_datasets` as the data source (URL-based source; declare types explicitly).
- Define a single Vega-Altair selection: an interval brush limited to the x (time) axis (`encodings=['x']`).
- Compose a vertically concatenated chart with exactly two views, with the detail (focus) view on top and the overview (context) view on the bottom.
- Upper detail view:
  - `mark_area`.
  - Encodes x as `date:T` whose x-scale `domain` is bound to the interval brush selection.
  - Encodes y as `price:Q`.
  - Width `600`, height `250`.
- Lower overview view:
  - Same `mark_area` over the same data (`date:T` -> `price:Q`).
  - Width `600`, height `70`.
  - The interval brush selection is attached to **this** view (it is the chart hosting the draggable brush).
- Save the resulting compound chart as a single self-contained HTML file using `chart.save(...)`.

## Implementation Hints
- Build a shared base `alt.Chart(data.sp500.url).mark_area().encode(...)` whose encodings can be reused across the two views; remember that URL-based data requires explicit type shorthands (e.g. `date:T`, `price:Q`).
- Use `alt.selection_interval(encodings=['x'])` to create the brush.
- For the upper view, override the x channel so that its scale `domain` references the brush selection (this is what makes the focus view rescale to the brushed region).
- For the lower view, attach the brush via `add_params(...)` so that the user can drag the interval on the context chart.
- Combine the two views vertically using `alt.vconcat` (or the `&` operator) with the focus chart on top and the context chart on the bottom.
- Use `chart.save('chart.html')` to write a self-contained HTML file that embeds the Vega-Lite spec and renders it with `vegaEmbed`.

## Acceptance Criteria
- Project path: /home/user/myproject
- Command: python3 build_chart.py
- The command must produce `/home/user/myproject/chart.html` containing a renderable Vega-Lite specification.
- The embedded Vega-Lite specification must:
  - Be a vertically concatenated chart with exactly two sub-views (a `vconcat` array of length 2), with the detail (focus) view first and the overview (context) view second.
  - Declare an interval selection parameter (a top-level `params` entry, or a view-level `params` entry) whose `select.type` is `"interval"` and whose `select.encodings` equals `["x"]`.
  - The first (upper) sub-view:
    - Has `mark` of type `"area"`.
    - Encodes x with field `date` of type `temporal` whose scale `domain` references the interval brush parameter (i.e. an object of the form `{"param": "<brush-name>"}` or `{"selection": "<brush-name>"}`).
    - Encodes y with field `price` of type `quantitative`.
    - Has `width == 600` and `height == 250`.
  - The second (lower) sub-view:
    - Has `mark` of type `"area"`.
    - Encodes x with field `date` of type `temporal` and y with field `price` of type `quantitative`.
    - Has `width == 600` and `height == 70`.
    - Has a `params` array containing the interval brush selection (the brush is attached to this view).
- Browser verification: Loading `chart.html` in a browser must render two stacked area charts (a large detail chart on top and a slim context chart on the bottom), with no JavaScript console errors. Dragging an interval on the lower context chart must visibly narrow the x-axis domain of the upper detail chart to the dragged region.

