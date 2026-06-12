# Back-to-Back Population Age Pyramid with Vega-Altair

## Background
You are building an interactive demographic explorer using Vega-Altair. The goal is to visualize the US population distribution as a back-to-back age pyramid for a single year, with a dropdown widget that lets the viewer switch between different census years from the canonical `data.population.url` dataset.

The dataset (`https://vega.github.io/vega-datasets/data/population.json`) has the columns:
- `year`: integer census year (1850, 1860, ..., 2000).
- `age`: integer age bucket (0, 5, 10, ..., 90).
- `sex`: 1 for male, 2 for female.
- `people`: number of people in that bucket.

## Requirements
- Build a Python script that generates a single Altair chart spec (no faceting, no horizontal concatenation) producing a classic back-to-back age pyramid:
  - Males extend to the left as negative bars, females extend to the right as positive bars.
  - The y axis lists `age` buckets with the oldest age at the top of the chart and the youngest at the bottom.
  - The x axis uses absolute-value labels even though the underlying data is signed (e.g., labels read `10M` on both sides, not `-10M` on the left).
  - Color encodes `sex` with a custom mapping: `1 -> Male` (e.g., steelblue) and `2 -> Female` (e.g., salmon). The legend must show the words "Male" and "Female", not the raw integers.
- The chart must include a `binding_select` dropdown bound to a single `alt.param`. The dropdown's options must be the distinct `year` values present in the dataset, and the chart must be filtered to a single year at a time. The initial selected year must be `1980`.
- The signed value used for the x axis must be computed inside the Vega-Lite spec via a `transform_calculate` step that produces a new field equal to `-people` when `sex == 1` (male) and `people` when `sex == 2` (female). Do **not** pre-compute this field in pandas; it has to live in the spec.
- Save the chart to `/home/user/myproject/pyramid.html` using Altair's `Chart.save(...)` API.
- Also write the underlying Vega-Lite spec (as returned by `Chart.to_dict()`) to `/home/user/myproject/pyramid_spec.json` so the verifier can inspect it.

## Implementation Hints
- The data source must be the URL string `data.population.url` from `altair.datasets` (not a pre-loaded Pandas DataFrame), so encoding type shorthands (`:Q`, `:O`, `:N`) are required.
- Use `transform_calculate` with a Vega expression that branches on `datum.sex` to build the signed field.
- Use `transform_filter` together with the year parameter so the dropdown actually controls the displayed year.
- For the x axis labels, look at the Vega-Lite axis options `format` and `labelExpr` (the latter receives `datum.value`).
- For the y axis ordering, use Altair's `sort` option on `alt.Y` to flip the natural ascending order of an ordinal axis.
- For the color legend wording, look at the `labelExpr` option of `alt.Color(...).legend(...)`.
- The script must be runnable as `python build_pyramid.py` from `/home/user/myproject` and must succeed without network access at *render* time (Altair only embeds the URL into the spec; no fetching is required to produce the HTML).

## Acceptance Criteria
- Project path: /home/user/myproject
- Command: python build_pyramid.py
- After running the command:
  - `/home/user/myproject/pyramid.html` must exist and be a self-contained HTML file produced by Altair (it must contain a `<script>` block with an embedded Vega-Lite spec).
  - `/home/user/myproject/pyramid_spec.json` must exist and contain the Vega-Lite spec as JSON.
- Vega-Lite spec requirements (checked against `pyramid_spec.json`):
  - The spec's `data` block references `https://vega.github.io/vega-datasets/data/population.json`.
  - There is a `transform_calculate` (a `calculate` transform) that produces a new field whose expression negates `people` when `sex == 1`.
  - There is a `transform_filter` that filters by the year parameter.
  - The mark is `bar`.
  - The `x` encoding is `quantitative`, uses the signed field, and its `axis` includes both `format` and `labelExpr` (with `labelExpr` referencing `abs(`).
  - The `y` encoding is `ordinal` over the `age` field, with a `sort` directive that places the largest age values at the top (one of `"descending"`, `"-age"`, or equivalent).
  - The `color` encoding is `nominal` over `sex`, with an explicit `scale` whose `domain` is `[1, 2]` and `range` is a two-element list of color names/codes, and a `legend` whose `labelExpr` maps `1 -> "Male"` and `2 -> "Female"`.
  - The spec contains exactly one parameter bound to a `binding_select`. Its options must include `1980`, and the parameter's initial `value` (or the selection's `init`) must be `1980`.
- Browser verification:
  - Open `pyramid.html` in a headless browser. After the Vega-Lite spec finishes rendering, the resulting DOM must contain:
    - At least one `<select>` element (the year dropdown injected by the `binding_select` widget).
    - At least one bar (SVG `path` or `rect` for the bar mark) whose horizontal extent is to the **left** of the x=0 baseline (a negative-extent bar for males) and at least one to the **right** (a positive-extent bar for females).

