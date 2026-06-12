"""
Build a US state-level engineers choropleth with Vega-Altair and save it as
a self-contained HTML file (chart.html) in the same directory as this script.
"""

import altair as alt
from vega_datasets import data

# ── Data sources ────────────────────────────────────────────────────────────
# TopoJSON geometry for US states (FIPS id on each feature)
states_topo = alt.topo_feature(data.us_10m.url, "states")

# Tabular dataset with columns: id (FIPS), state, engineers, hurricanes, …
engineers_url = data.population_engineers_hurricanes.url

# ── Chart ───────────────────────────────────────────────────────────────────
chart = (
    alt.Chart(states_topo)
    .mark_geoshape()
    .transform_lookup(
        lookup="id",
        from_=alt.LookupData(
            data=engineers_url,
            key="id",
            fields=["state", "engineers"],
        ),
    )
    .encode(
        color=alt.Color(
            "engineers:Q",
            scale=alt.Scale(scheme="blues"),
            title="Engineers",
        ),
        tooltip=[
            alt.Tooltip("state:N", title="State"),
            alt.Tooltip("engineers:Q", title="Engineers", format=","),
        ],
    )
    .project(type="albersUsa")
    .properties(
        width=700,
        height=400,
        title="US Engineers by State",
    )
)

# ── Export ───────────────────────────────────────────────────────────────────
output_path = "chart.html"
chart.save(output_path)
print(f"Saved → {output_path}")
