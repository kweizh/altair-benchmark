# Iris Petal Length Histogram by Species with Vega-Altair

## Background
Build a binned histogram of `petalLength` from the iris dataset using Vega-Altair, with bars colored by `species` and stacked using Vega-Lite's default stacking behavior. The chart must be exported to a self-contained HTML file that fully renders in a browser.

## Requirements
- Use `data.iris.url` from `vega_datasets` as the data source (URL-based source; declare types explicitly).
- Build a single (non-layered) chart with `mark_bar`.
- Bin the `petalLength` field on the x axis with `maxbins=20`.
- Aggregate `count()` on the y axis (no manual pre-aggregation).
- Encode bar color by `species` as a nominal field.
- Bars must be stacked using the default Vega-Lite stacking behavior (do not disable stacking).
- Save the resulting chart as a single self-contained HTML file using `chart.save(...)`.

## Implementation Hints
- Build a chart from `alt.Chart(data.iris.url)`; remember that URL-based data requires explicit type shorthands (e.g. `petalLength:Q`, `species:N`).
- The x channel must use Altair's binning helper to apply `maxbins=20` to the `petalLength` field; the y channel must use the `count()` aggregate.
- The color channel must reference the nominal `species` field so that each species gets its own color and shows up in the legend.
- The bars are stacked by default in Vega-Lite when a quantitative axis is aggregated and a categorical color encoding is present; there is no need to explicitly disable stacking.
- The HTML must contain the Vega-Lite spec embedded in a `<script type="application/json">` block or via a `var spec = {...};` declaration consumed by `vegaEmbed`.

## Acceptance Criteria
- Project path: /home/user/myproject
- Command: python3 build_chart.py
- The command must produce `/home/user/myproject/chart.html` containing a renderable Vega-Lite specification.
- The embedded Vega-Lite specification must:
  - Use `mark` of type `bar`.
  - Define `encoding.x` over the `petalLength` (or `petal_length`) field as quantitative with a `bin` object whose `maxbins` is `20`.
  - Define `encoding.y` as the `count` aggregate (no explicit field required for the count aggregate).
  - Define `encoding.color` over the `species` field as nominal.
- Browser verification: Loading `chart.html` in a browser must render the chart with no JavaScript console errors. The rendered chart must show stacked colored bars (three distinct species colors) along the x axis, and the legend must list three species (`setosa`, `versicolor`, `virginica`).

