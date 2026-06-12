# Faceted Penguins Scatter with Legend-Toggle Interaction

## Background
You are exploring the Palmer penguins dataset with Vega-Altair. To compare species within each island side-by-side while still being able to focus on a single species across all islands, build a faceted scatter chart that lets the viewer toggle species visibility through the legend.

## Requirements
- Load the penguins dataset from `vega_datasets` (`from vega_datasets import data; data.penguins()`).
- Build a faceted scatter plot:
  - One panel per `Island`, arranged as columns.
  - Each panel plots `Beak Length (mm)` on the x-axis against `Body Mass (g)` on the y-axis.
  - Points are colored by `Species`.
- Add a point selection that is projected over the `Species` field and bound to the chart's legend, so that clicking a legend entry toggles the corresponding species across every facet panel.
- Drive the marks' `opacity` encoding from that selection: points that match the selected species are fully opaque, all other points are dimmed (use a small opacity such as ~0.1).
- Resolve the y scale independently for each facet panel.
- Configure both x and y scales so they do not include zero.
- Save the chart to:
  - `/home/user/myproject/chart.html` — the rendered, embeddable HTML (used for browser verification).
  - `/home/user/myproject/chart.json` — the Vega-Lite specification produced by Altair (e.g. via `chart.to_dict()` or `chart.to_json()`).

## Implementation Hints
- Use `alt.Chart(...).mark_point().encode(...)` to build a single base scatter, then compose it into a faceted chart with `.facet(...)`.
- The legend-driven selection should be a point selection projected over a single field. Refer to Altair's selection / parameter docs and the Vega-Lite `bind: "legend"` pattern.
- Use `alt.condition(...)` (or the equivalent `alt.when(...).then(...).otherwise(...)`) on the `opacity` channel so that the selection drives opacity rather than color.
- Per-panel y axes are controlled through scale resolution at the compound-chart level.
- Use `alt.X(...).scale(zero=False)` and `alt.Y(...).scale(zero=False)` to keep both axes from including zero.
- Save the spec JSON exactly as Altair emits it; do not hand-edit the JSON. Use `chart.save('chart.html')` (and `chart.to_dict()` / `chart.to_json()` for the JSON file).

## Acceptance Criteria
- Project path: /home/user/myproject
- Ensure the script is executed and the artifacts exist.
- Output artifacts:
  - `/home/user/myproject/chart.html` — standalone HTML produced by Altair that embeds the Vega-Lite spec via vegaEmbed.
  - `/home/user/myproject/chart.json` — the Vega-Lite specification of the same chart.
- The Vega-Lite specification must satisfy all of the following:
  - It is a faceted chart whose column facet is the `Island` field.
  - It declares a point selection (Vega-Lite `param`) with:
    - `select.type = "point"`
    - `select.fields` containing exactly `"Species"`
    - `bind = "legend"` (string `"legend"` or an object `{ "legend": ... }`)
  - The `opacity` encoding is a `condition` that references that param by name. The selected branch uses a high opacity (1, or very close to 1) and the unselected branch uses a low opacity (around 0.1, and strictly less than 0.5).
  - The chart's `resolve.scale.y` is set to `"independent"`.
  - Both the x and y scales explicitly set `zero` to `false`.
  - The data points are colored by `Species` and plotted with `Beak Length (mm)` on x and `Body Mass (g)` on y.
- Browser verification on `/home/user/myproject/chart.html`:
  - The page renders at least 3 facet panels (one per island).
  - A legend for `Species` is present and its symbols are clickable / interactive (cursor changes or click events are wired up).

