Combining faceted charts with shared interactive selections often leads to axis scale conflicts or unexpected behaviors if scales are not properly resolved.

You need to create a faceted scatter plot (faceted by "Origin" into separate columns) of the `cars` dataset where a legend-bound point selection highlights specific "Cylinders" across all facets simultaneously.

**Constraints:**
- You MUST ensure the Y-axis is optimized for each facet by using `resolve_scale(y='independent')`.
- You MUST use `alt.selection_point(fields=['Cylinders'], bind='legend')` to create the interactivity.
- The opacity of points not matching the legend selection must drop to `0.2` across all facets.
- Save the resulting chart specification to `faceted_shared.json`.