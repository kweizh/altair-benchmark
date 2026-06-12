# World Population Bubble Map with Year Slider (Vega-Altair)

## Background
Build an interactive world map that visualizes country populations over time using Vega-Altair. The chart must combine a TopoJSON country base layer with a population bubble overlay and a year slider, then be saved to an HTML file that can be opened and exercised in a web browser.

## Requirements
- Write a Python script that uses Vega-Altair to construct a single chart and save it as an HTML file.
- Base layer: a world country base map rendered with `mark_geoshape` styled with `fill='#eeeeee'` and `stroke='white'`, sourced from `alt.topo_feature(data.world_110m.url, 'countries')`.
- Overlay: `mark_circle` bubbles representing country populations from the gapminder dataset at `data.gapminder.url`. Country centroids must be supplied by a separate dataset (you may inline a small lookup table) and joined to the gapminder rows via `transform_lookup`.
- Encodings on the bubble layer:
  - `longitude` and `latitude` come from the looked-up centroid fields.
  - `size` encodes `pop:Q` with a **fixed** quantitative scale `domain` whose upper bound is the maximum population across all years in the dataset, so bubbles stay comparable across years.
  - `color` encodes `cluster:N`.
- Year slider: add an `alt.param` bound to `alt.binding_range(min=1955, max=2005, step=5, name='Year')` and apply a `transform_filter` so only rows whose `year` field equals the current parameter value are shown. The slider must appear in the HTML output as a real `<input type="range">` element.
- Use the `naturalEarth1` projection on the chart that contains both layers.
- Save the chart to `chart.html` next to the script. The HTML must include both the geoshape paths and the circle marks for at least one year value.

## Implementation Hints
- Compose the geoshape base and the circle overlay as a single layered Altair chart (or a layered chart inside a single-cell hconcat) so that the projection applies to both layers.
- The gapminder dataset has fields `year`, `country`, `cluster`, `pop`, `life_expect`, `fertility`. The world-110m TopoJSON features are keyed by ISO numeric `id`, not by name, so map between them however you find convenient (e.g., an inline `alt.Data(values=[...])` centroid table keyed by `country`).
- `transform_filter` accepts a Vega-Lite expression string; reference the slider parameter by name and compare to `datum.year`.
- Compute the population scale domain once in Python from the gapminder data so it covers every year (1955-2005, step 5).
- Save with `chart.save('chart.html')`. A simple `python3 build_chart.py` invocation should regenerate the file.

## Acceptance Criteria
- Project path: /home/user/myproject
- Command: `python3 build_chart.py`
- After running the command, the file `/home/user/myproject/chart.html` must exist.
- The generated HTML file must contain:
  - At least one `<svg>` `<path>` element from the country geoshape layer.
  - At least one rendered circle mark (an SVG `<circle>` or `<path>` produced by `mark_circle`).
  - A `<input ... type="range">` slider widget tied to the year parameter, with min `1955`, max `2005`, and step `5`.
- A Python file `/home/user/myproject/spec.json` must also be produced (by the same script) containing `chart.to_json()` output; this file is used for structural verification.
- The Vega-Lite spec written to `spec.json` must satisfy:
  - The top-level chart is layered (`layer`) or a single-cell `hconcat`/`vconcat` containing a layered chart, with both a `geoshape` mark and a `circle` mark.
  - The chart-level `projection.type` is `"naturalEarth1"`.
  - The top-level `params` array contains at least one entry whose `bind` is a `binding_range` with `min: 1955`, `max: 2005`, `step: 5`.
  - At least one `transform_filter` references both the year parameter name and the field `year`.
  - The bubble layer's `size` channel has an explicit `scale.domain` (a two-element list starting at 0).

