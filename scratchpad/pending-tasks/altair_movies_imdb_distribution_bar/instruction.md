# IMDB Rating Distribution Histogram with Vega-Altair

## Background
Build a Vega-Altair histogram of `IMDB_Rating` from the movies dataset. The chart filters out rows where `IMDB_Rating` is null inside the Vega-Lite spec (not pre-processed in pandas) and bins the remaining ratings into fixed-width buckets. The chart must be exported to a static HTML file that fully renders in a browser.

## Requirements
- Use `data.movies.url` from `vega_datasets` as the data source (URL-based source; declare types explicitly).
- Render a `mark_bar` histogram of `IMDB_Rating`.
- Bin the x-axis with a fixed `step` of `0.5` (e.g. 1.0-1.5, 1.5-2.0, ...).
- The y-axis must be an aggregated `count` of records per bin.
- Inside the spec, pre-filter rows where `IMDB_Rating` is null using a `transform_filter` whose expression references `IMDB_Rating` and excludes nulls (e.g. `alt.datum.IMDB_Rating != None` or an equivalent Vega expression).
- Set the chart title to exactly `"IMDB Rating Distribution"`.
- Save the resulting chart as a single self-contained HTML file using `chart.save(...)`.

## Implementation Hints
- Build `alt.Chart(data.movies.url)` and use the method-based `bin` syntax with a fixed step (`alt.X('IMDB_Rating:Q').bin(step=0.5)`).
- Use a `count` aggregate on the y channel, e.g. `y='count()'`.
- Use `alt.datum.IMDB_Rating` inside `transform_filter(...)` to drop nulls before binning; remember the `!=` operator compiles to a Vega expression string with `null`.
- Use `.properties(title="IMDB Rating Distribution")` to set the title.
- Save the chart via `chart.save("chart.html")`; the HTML must embed the Vega-Lite spec (e.g. via `vegaEmbed`).

## Acceptance Criteria
- Project path: /home/user/myproject
- Command: python3 build_chart.py
- The command must produce `/home/user/myproject/chart.html` containing a renderable Vega-Lite specification.
- The embedded Vega-Lite specification must:
  - Have a `mark` of type `bar`.
  - Encode `x` against the `IMDB_Rating` field with a `bin` definition whose `step` is `0.5`.
  - Encode `y` with `aggregate` equal to `"count"`.
  - Define at least one top-level `transform` entry of type `filter` whose filter expression references `IMDB_Rating` and excludes null values.
  - Set the top-level `title` to exactly `"IMDB Rating Distribution"`.
- Browser verification: Loading `chart.html` in a browser must render the chart without JavaScript console errors; the rendered output must show multiple bars distributed across IMDB rating values along the x-axis.

