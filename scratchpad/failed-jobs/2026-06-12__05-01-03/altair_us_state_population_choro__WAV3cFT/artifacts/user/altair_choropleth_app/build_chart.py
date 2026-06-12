"""
build_chart.py
==============
Generates a self-contained Altair choropleth map of the United States where
the viewer can switch the displayed metric (population, engineers, hurricanes)
via a dropdown control.

Run:
    python build_chart.py

Output:
    chart.html  –  single self-contained HTML file
"""

import altair as alt

# ---------------------------------------------------------------------------
# Dataset URLs
# ---------------------------------------------------------------------------
data = alt.datasets.data
topo_url = data.us_10m.url          # TopoJSON – us-10m.json
values_url = data.population_engineers_hurricanes.url  # CSV with per-state values

# ---------------------------------------------------------------------------
# Dropdown parameter
# ---------------------------------------------------------------------------
# The parameter stores the name of the column the user has chosen.
metric_options = ["population", "engineers", "hurricanes"]

metric_param = alt.param(
    name="metric",
    value="population",
    bind=alt.binding_select(
        options=metric_options,
        name="Metric: ",
    ),
)

# ---------------------------------------------------------------------------
# Base geoshape chart
# ---------------------------------------------------------------------------
choropleth = (
    alt.Chart(alt.topo_feature(topo_url, "states"))
    .mark_geoshape(stroke="white", strokeWidth=0.75)
    # ── Pull all three numeric columns + state name onto every feature ──
    .transform_lookup(
        lookup="id",
        from_=alt.LookupData(
            data=values_url,
            key="id",
            fields=["state", "population", "engineers", "hurricanes"],
        ),
    )
    # ── Project the chosen column to a single synthetic field ──
    .transform_calculate(
        chosen_metric="datum[metric]",
    )
    # ── Encodings ──
    .encode(
        color=alt.Color(
            "chosen_metric:Q",
            title="Value",
            scale=alt.Scale(scheme="blues"),
            legend=alt.Legend(orient="bottom-right"),
        ),
        tooltip=[
            alt.Tooltip("state:N", title="State"),
            alt.Tooltip("chosen_metric:Q", title="Value", format=","),
        ],
    )
    # ── Projection ──
    .project(type="albersUsa")
    # ── Attach the parameter so the dropdown is part of this chart ──
    .add_params(metric_param)
    .properties(
        width=800,
        height=500,
        title=alt.TitleParams(
            text="US State Choropleth – Interactive Metric Switcher",
            fontSize=16,
            anchor="middle",
        ),
    )
)

# ---------------------------------------------------------------------------
# Save as self-contained HTML
# ---------------------------------------------------------------------------
output_path = "chart.html"
choropleth.save(output_path)
print(f"Chart saved → {output_path}")
