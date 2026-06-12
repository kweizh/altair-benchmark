# Penguins SPLOM with Linked Brushing (Vega-Altair)

## Background
You are building an exploratory visual analytics view for the Palmer Penguins dataset using Vega-Altair. The goal is a Scatter PLOt Matrix (SPLOM) with a single, globally-resolved interval brush so that an analyst can drag a rectangle in any cell and instantly see which observations are highlighted across every cell, colored by species.

## Requirements
- Build a SPLOM using `alt.repeat(row=[...], column=[...])` over the four quantitative penguin features: `Beak Length (mm)`, `Beak Depth (mm)`, `Flipper Length (mm)`, and `Body Mass (g)`.
- Both the `row` repeat list and the `column` repeat list must contain all four features (so the matrix has 4 rows and 4 columns of cells).
- Each cell must use `mark_point` with x and y bound to the repeated row/column field (quantitative type).
- Both x and y scales must use `zero=False` so the axes tightly frame the data.
- Add a single `alt.selection_interval` parameter projected over both `x` and `y` encodings (`encodings=['x','y']`). The brush must be a single global brush across the whole SPLOM.
- The point color encoding must be conditional on the brush: when a point is inside the brush, color it by `Species` (nominal); otherwise color it `lightgray`. Use `alt.condition` or `alt.when` against the brush parameter.
- Render the chart to a self-contained HTML file at `/home/user/myproject/chart.html`.

## Implementation Hints
- The Penguins dataset is bundled with the `vega_datasets` package as `data.penguins.url` and uses spaces and parentheses in its column names; quote them exactly when listing repeat fields.
- Inside the encoded `alt.X` / `alt.Y`, use `alt.repeat('column')` / `alt.repeat('row')` and remember to declare `type='quantitative'` because the data is loaded by URL.
- Attach the brush parameter to the chart with `add_params(...)` before calling `.repeat(...)`.
- For a single brush shared across all cells, the interval selection defaults to a global resolve which is what you want here.
- Use `chart.save('chart.html')` (or equivalent) so the produced HTML embeds the Vega-Lite spec and renders in a browser via `vega-embed`.

## Acceptance Criteria
- Project path: /home/user/myproject
- Command: python3 /home/user/myproject/solution.py
- The command must write the output HTML file to: /home/user/myproject/chart.html
- The generated HTML must contain an embedded Vega-Lite spec whose `repeat` block defines a `row` array AND a `column` array, each of length at least 3 (the reference solution uses 4).
- The repeated spec must use `mark` of type `point`.
- The repeated spec must declare an interval selection parameter (Vega-Lite `select.type == 'interval'`) whose `encodings` include both `x` and `y`.
- The color encoding in the repeated spec must be a conditional encoding that references the brush parameter (i.e. it uses a `condition` clause keyed on the selection `param`).
- Both the x and y scales in the repeated spec must set `zero` to `false`.
- Browser verification: when the saved HTML is rendered headlessly, the page must contain at least 9 distinct scatter cells (SVG/canvas plotting groups produced by the repeat operator) and an interval-selection brush layer must be present.

