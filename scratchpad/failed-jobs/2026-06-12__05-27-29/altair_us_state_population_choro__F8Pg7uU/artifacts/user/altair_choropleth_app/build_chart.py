"""
Build a US state-level choropleth map with a metric-switching dropdown.

The chart uses the population_engineers_hurricanes dataset and lets the
viewer toggle between population, engineers, and hurricanes via a dropdown.
"""

import altair as alt
from vega_datasets import data

# ── Data sources ──────────────────────────────────────────────────────
states = alt.topo_feature(data.us_10m.url, feature="states")

# ── Dropdown parameter ───────────────────────────────────────────────
dropdown = alt.binding_select(
    options=["population", "engineers", "hurricanes"],
    name="Metric: ",
)

metric_param = alt.param(
    value="population",
    bind=dropdown,
    name="metric_choice",
)

# ── Choropleth chart ─────────────────────────────────────────────────
chart = (
    alt.Chart(states)
    .mark_geoshape(stroke="white")
    .encode(
        color=alt.Color("metric:Q", title="Value"),
        tooltip=[
            alt.Tooltip("state:N", title="State"),
            alt.Tooltip("metric:Q", title="Value", format=","),
        ],
    )
    .transform_lookup(
        lookup="id",
        from_=alt.LookupData(
            data.population_engineers_hurricanes.url,
            "id",
            ["population", "engineers", "hurricanes", "state"],
        ),
    )
    .transform_calculate(
        metric="datum[metric_choice]",
    )
    .project(type="albersUsa")
    .add_params(metric_param)
    .properties(
        width=900,
        height=550,
        title="US State Choropleth – Switchable Metric",
    )
)

# ── Persist as self-contained HTML ────────────────────────────────────
output_path = "/home/user/altair_choropleth_app/chart.html"
chart.save(output_path)
print(f"Chart saved to {output_path}")