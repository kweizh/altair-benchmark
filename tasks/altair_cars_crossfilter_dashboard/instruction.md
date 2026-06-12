# Cross-Filtering Dashboard on the Cars Dataset with Vega-Altair

## Background
Vega-Altair is a declarative statistical visualization library for Python that compiles to Vega-Lite. In this task you will build a cross-filtering interactive dashboard for the classic `cars` dataset (available as `vega_datasets.data.cars`). The dashboard has three linked views composed with Altair's view-composition operators, and an interval brush in the scatter view that drives `transform_filter` in the other two views.

## Requirements
Produce a single Python entry-point at `/home/user/myproject/solution.py` that, when executed, builds the chart and writes a Vega-embed HTML file to `/home/user/myproject/chart.html`.

The rendered chart must contain exactly three sub-views, composed in the layout `(A | B) & C`:

- **View A — Scatter (`mark_point`)**
  - x: `Horsepower` (quantitative)
  - y: `Miles_per_Gallon` (quantitative)
  - color: `Origin` (nominal)
  - An interval brush selection over BOTH the x and y encoding channels, attached to this view via `add_params(...)`.
- **View B — Horizontal bar chart (`mark_bar`)**
  - y: `Origin` (nominal)
  - x: `count()` aggregate (quantitative)
  - Must be filtered by the brush defined in View A using `transform_filter(brush)`.
- **View C — Binned 2D heatmap (`mark_rect`)**
  - x: `Weight_in_lbs`, binned
  - y: `Acceleration`, binned
  - color: `count()` aggregate (quantitative)
  - Must be filtered by the brush defined in View A using `transform_filter(brush)`.

Compose the three views as `(A | B) & C` using Altair's `|` and `&` operators (so the top-level Vega-Lite spec is a `vconcat` whose first row is an `hconcat` of A and B, and whose second row is C).

## Implementation Hints
- Use `vega_datasets.data.cars` (or `data.cars.url`) as the input data.
- Define one `selection_interval` (Altair 5+ API) and attach it with `add_params(...)` on View A; reuse the same selection inside `transform_filter(...)` on Views B and C so brushing in A cross-filters B and C.
- For View C, use Altair's binning API on both encoding channels (e.g. `alt.X('Weight_in_lbs').bin()` and `alt.Y('Acceleration').bin()`).
- Save the chart with `chart.save('/home/user/myproject/chart.html')` so that the resulting HTML embeds the full Vega-Lite spec.
- Avoid hard-coding visual styling such as widths, fonts, color palettes, or titles — the verifier intentionally ignores these.

## Acceptance Criteria
Project path: /home/user/myproject
Command: python solution.py
Artifact: /home/user/myproject/chart.html

The verifier extracts the embedded Vega-Lite JSON spec from `chart.html` and checks:

- The top-level spec uses `vconcat` containing exactly 2 entries; the first entry uses `hconcat` containing exactly 2 entries. (Layout = `(A | B) & C`.)
- View A (first entry inside `hconcat`):
  - mark is `point`.
  - encoding `x.field == 'Horsepower'`, `y.field == 'Miles_per_Gallon'`, `color.field == 'Origin'`.
  - declares at least one parameter whose `select.type == 'interval'` and whose `select.encodings` contains both `'x'` and `'y'`.
- View B (second entry inside `hconcat`):
  - mark is `bar`.
  - one of its x/y encodings has `field == 'Origin'`; the opposite axis has `aggregate == 'count'`.
  - its `transform` list contains a filter whose `filter.param` matches the brush parameter name declared in View A.
- View C (second entry of the top-level `vconcat`):
  - mark is `rect`.
  - both `x` and `y` encodings have a truthy `bin` property; `x.field == 'Weight_in_lbs'` and `y.field == 'Acceleration'`.
  - color encoding has `aggregate == 'count'`.
  - its `transform` list contains a filter whose `filter.param` matches the brush parameter name declared in View A.

In addition, a browser verification step opens `chart.html` through a local HTTP server, waits for the Vega-embed runtime to render, and confirms that three sub-views are visible and that dragging in the scatter view updates both the bar chart and the heatmap (cross-filter behavior).

