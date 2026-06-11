Interactive "Focus + Context" charts allow users to zoom in on specific temporal or quantitative data regions without losing sight of the overall trend, leveraging Altair's selection APIs.

You need to implement an interactive chart using Altair v5+ syntax where a small overview area chart includes an interval brush that dynamically controls the X-axis domain of a larger detailed line chart.

**Constraints:**
- MUST use Altair v5+ syntax, specifically `alt.selection_interval()` and `add_params()` (do NOT use the deprecated `add_selection`).
- The two charts must be vertically concatenated using the `&` operator.
- The X-axis of the detail chart must strictly bind to the brush parameter from the overview chart.
- Save the resulting chart specification to `focus_context.json`.