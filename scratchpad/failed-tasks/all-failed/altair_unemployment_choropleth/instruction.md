# US County Unemployment Choropleth with Linked Brushable Histogram

## Background
Build an interactive geographic dashboard in Vega-Altair (Python) that visualizes the 2018 US county-level unemployment rate as a choropleth map joined with a brushable histogram. The dashboard must combine a TopoJSON geographic layer with a separate tabular rate dataset using a lookup transform, an Albers USA projection, a threshold (binned) color scale, and a cross-view interval brush filter.

## Requirements
- Use `vega-altair` to build a `vconcat` (or `hconcat`) dashboard composed of:
  1. A US county choropleth rendered with `mark_geoshape()`.
  2. A histogram of the unemployment `rate` rendered with `mark_bar()` that exposes an interval brush on its x-axis.
- The map must:
  - Use `alt.topo_feature(data.us_10m.url, 'counties')` as its primary data source.
  - Use a `transform_lookup` that joins the county geometries to `data.unemployment.url` on `id` and pulls in the `rate` field.
  - Project with `albersUsa`.
  - Encode `color` from the looked-up `rate` field as quantitative, using a `threshold` scale (with a `domain` of at least three break points, e.g. `[0.05, 0.10, 0.15, 0.20]`) and a sequential `blues` color scheme.
  - Include a tooltip exposing both the county `id` and `rate`.
  - Apply a `transform_filter` that filters the displayed counties to the brush selection on the histogram.
- The histogram must:
  - Read directly from `data.unemployment.url` (so all counties are visible in the histogram even when the map is filtered).
  - Bin the `rate` field on the x-axis and count rows on the y-axis (`mark_bar()`).
  - Carry an `alt.selection_interval(encodings=['x'])` parameter added with `add_params(...)`. The same parameter must be referenced by the map's `transform_filter`.
- Save the final chart as an interactive HTML file using `chart.save('chart.html')` (any embed options are fine; the default canvas renderer is acceptable as long as a `<script>` tag containing the Vega-Lite spec is embedded in the HTML).
- Wrap everything in a runnable script at `/home/user/myproject/solution.py`.

## Implementation Hints
- Refer to Altair's Geoshape, Choropleth Classification, and Lookup transform documentation for the correct API usage.
- Counties in `us_10m` join to the unemployment table via the FIPS `id` field.
- The threshold scale should produce a banded/categorical legend with discrete bins.
- The interval brush parameter must be created once and reused by both the histogram (`add_params`) and the map (`transform_filter`).
- The generated HTML file embeds the Vega-Lite spec inside a JSON object passed to `vegaEmbed`; downstream verification will parse that spec.

## Acceptance Criteria
- Project path: /home/user/myproject
- Command: `python3 solution.py`
- Running the command must write a non-empty `chart.html` file to `/home/user/myproject/chart.html`.
- The embedded Vega-Lite specification inside `chart.html` must satisfy all of the following structural properties:
  - Contains a `geoshape` mark whose chart has a `transform` list including a `lookup` step referencing the `unemployment` dataset (URL contains the substring `unemployment`).
  - The geoshape chart's `projection.type` is `albersUsa`.
  - The geoshape chart's `color` encoding references a numeric `rate` field with a `threshold`-type scale and a `blues` color scheme.
  - The geoshape chart's `tooltip` encoding exposes both `id` and `rate` fields.
  - The geoshape chart includes a `filter` transform that references a selection parameter name (e.g. via `{"param": "<name>"}`).
  - A separate chart in the same spec uses a `bar` mark, contains a binned x-encoding on the `rate` field, and registers a `params` entry whose `select.type` is `interval` (the same param name referenced by the map's filter).
- Browser verification (via `pochi-verifier`): When `chart.html` is opened in a headless browser, the rendered DOM must contain at least one SVG/canvas element produced by Vega-Embed (`#vis` container) and the page must not raise JavaScript errors.

