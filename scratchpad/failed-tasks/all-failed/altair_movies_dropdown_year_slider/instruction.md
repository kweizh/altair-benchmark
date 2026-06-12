# Interactive Movies Dashboard with Vega-Altair Widgets

## Background
Build an interactive movies dashboard that uses Vega-Altair widget bindings (a dropdown and a range slider) to explore a published movies dataset directly from its URL. The dashboard renders to a self-contained HTML file that loads the data in the browser via Vega-Embed.

## Requirements
- Use Vega-Altair (v5+) with the URL source `vega_datasets.data.movies.url` (do not download or pre-process the data with pandas).
- Produce a single scatter chart of `Production_Budget` on the x axis vs `Worldwide_Gross` on the y axis, both rendered with logarithmic scales.
- Color points by `Major_Genre`.
- Provide a title and human-readable axis labels.
- Expose two bound interaction widgets, both declared with `alt.param`:
  1. A `alt.binding_select` dropdown for `Major_Genre`. The options must include every distinct genre in the dataset PLUS an `"All"` entry that disables genre filtering.
  2. A `alt.binding_range` slider for the release year, with `min=1980`, `max=2020`, `step=1`.
- Filter the data by the genre param via `transform_filter` (when the dropdown is `"All"`, no genre filtering is applied).
- Highlight points whose computed `Release_Year` equals the slider value by using `alt.when(...).then(<Major_Genre color>).otherwise(alt.value('lightgray'))` (or the equivalent `alt.condition(...)`) on the color encoding.
- The release year must be computed inside the spec from `Release_Date` via `transform_calculate` (do not pre-compute it in Python).
- Save the rendered dashboard to `/home/user/project/movies_dashboard.html` using `Chart.save(...)`.

## Implementation Hints
- The dataset is loaded by URL, so encoding field types must be declared explicitly (e.g. `Production_Budget:Q`).
- Use `alt.param(bind=alt.binding_select(options=[...], name='Genre: '))` and `alt.param(bind=alt.binding_range(min=1980, max=2020, step=1, name='Release Year: '))`.
- Remember to attach both params to the chart with `.add_params(...)`.
- The dataset's `Release_Date` field is a date-like string. You can extract the year inside the spec using a Vega expression such as `year(datum.Release_Date)` (after coercing to a date) or by parsing the field with `alt.UrlData(..., format=alt.DataFormat(parse={...}))`.
- For the "All" option, use a `transform_filter` whose predicate is true when the dropdown param equals `'All'` and otherwise compares against `datum.Major_Genre`.
- Inspect the produced Vega-Lite JSON via `Chart.to_dict()` if you need to debug param/encoding wiring.

## Acceptance Criteria
- Project path: /home/user/project
- Command: python3 /home/user/project/build_dashboard.py
- The command must (re)generate `/home/user/project/movies_dashboard.html` on every run.
- The generated HTML must:
  - Be openable in a headless browser and produce a Vega view (i.e. `vegaEmbed` must successfully render the chart with no JS errors).
  - Contain a `<select>` element (the genre dropdown injected by Vega-Embed's binding controls).
  - Contain an `<input type="range">` element (the year slider injected by Vega-Embed's binding controls).
- The Vega-Lite spec embedded in the HTML must:
  - Reference `vega_datasets.data.movies.url` (or an equivalent jsdelivr CDN URL ending in `data/movies.json`) as its data source.
  - Declare exactly two top-level `params`, one with a `binding` of type `select` whose `options` include the string `"All"`, and one with a `binding` of type `range` with `min=1980`, `max=2020`, `step=1`.
  - Contain a `transform_filter` whose predicate string references the genre param name.
  - Contain a `transform_calculate` that produces a `Release_Year` field from `Release_Date`.
  - Use `"scale": {"type": "log"}` on both the x and y encodings.
  - Use a conditional color encoding (`condition`) whose `test` references the slider param name and whose `value` (else branch) is the string `"lightgray"`.

