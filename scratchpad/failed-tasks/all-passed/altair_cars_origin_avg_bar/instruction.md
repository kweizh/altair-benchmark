# Average MPG by Origin Bar Chart with Vega-Altair

## Background
Build a simple but precise Vega-Altair bar chart showing the average `Miles_per_Gallon` per `Origin` from the classic `cars` dataset. The chart must sort bars by mean MPG (highest first) and show a custom tooltip that reveals both the mean MPG and the number of cars contributing to each bar. Export the chart to a static HTML file that fully renders in a browser.

## Requirements
- Use `data.cars.url` from `vega_datasets` as the data source (URL-based source; declare types explicitly using shorthand suffixes such as `Origin:N` and `Miles_per_Gallon:Q`).
- Render a single (non-layered, non-faceted, non-concatenated) bar chart using `mark_bar`.
- Map `Origin` to the x channel as a nominal field, and the mean of `Miles_per_Gallon` to the y channel as a quantitative field.
- Sort the x axis by the mean of `Miles_per_Gallon` in descending order (Origin with the highest mean MPG first).
- Provide a custom `tooltip` channel that is a list with BOTH:
  1. The mean of `Miles_per_Gallon` (aggregate `mean` over `Miles_per_Gallon`), and
  2. The count of cars per origin (aggregate `count`).
- Save the resulting chart as a self-contained HTML file using `chart.save(...)`.

## Implementation Hints
- Build a single chart from `alt.Chart(data.cars.url).mark_bar()`; remember that URL-based data requires explicit type shorthands.
- For the x sort, use the encoding helper `alt.X('Origin:N').sort(field='Miles_per_Gallon', op='mean', order='descending')`, or the shorthand `sort='-y'` against a y channel that already aggregates `mean(Miles_per_Gallon)`.
- For the tooltip channel, pass a Python list of two entries; each entry may use either the shorthand string syntax (e.g. `'mean(Miles_per_Gallon):Q'`, `'count():Q'`) or `alt.Tooltip(...)` with explicit `aggregate` and `field`.
- The output HTML must contain the Vega-Lite spec embedded in the standard Altair template (a `var spec = {...};` block or a `<script type="application/json">` block) and must be renderable by `vegaEmbed`.

## Acceptance Criteria
- Project path: /home/user/myproject
- Command: python3 build_chart.py
- The command must produce `/home/user/myproject/chart.html` containing a renderable Vega-Lite specification.
- The embedded Vega-Lite specification must:
  - Be a single bar chart whose top-level `mark` is `bar` (string `"bar"` or object with `"type": "bar"`). It must NOT use `layer`, `concat`, `hconcat`, `vconcat`, `facet`, or `repeat` at the top level.
  - Have `encoding.x` with `field == "Origin"` and `type == "nominal"`.
  - Have `encoding.y` that aggregates `mean` over `field == "Miles_per_Gallon"` (quantitative).
  - Sort the x axis by mean `Miles_per_Gallon` in descending order. Either:
    - `encoding.x.sort` is an object with `op == "mean"`, `field == "Miles_per_Gallon"`, and `order == "descending"`, OR
    - `encoding.x.sort` is the shorthand string `"-y"` and the y channel already aggregates `mean(Miles_per_Gallon)`.
  - Have `encoding.tooltip` as an array of at least two entries that includes BOTH:
    1. An entry with `aggregate == "mean"` over `field == "Miles_per_Gallon"`, AND
    2. An entry with `aggregate == "count"` (the `field` may be `*` or any other value, as is standard for `count()`).
- Browser verification: Loading `chart.html` in a browser must render the chart without JavaScript console errors. The rendered chart must display exactly 3 vertical bars for the three origins `Europe`, `Japan`, and `USA`, with bar heights monotonically decreasing from left to right (descending mean MPG).

