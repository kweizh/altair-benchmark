import altair as alt
from vega_datasets import data

# Load US state geometries from TopoJSON
states_topo = alt.topo_feature(data.us_10m.url, "states")

# Lookup data source for engineers/hurricanes dataset
lookup_data = alt.LookupData(
    data.population_engineers_hurricanes.url,
    key="id",
    fields=["engineers", "state"],
)

# Build the choropleth chart
chart = (
    alt.Chart(states_topo)
    .mark_geoshape()
    .encode(
        color=alt.Color(
            "engineers:Q",
            scale=alt.Scale(scheme="blues"),
            title="Engineers",
        ),
        tooltip=[
            alt.Tooltip("state:N", title="State"),
            alt.Tooltip("engineers:Q", title="Engineers"),
        ],
    )
    .transform_lookup(lookup="id", from_=lookup_data)
    .project(type="albersUsa")
    .properties(width=700, height=400)
)

# Save as self-contained HTML
chart.save("/home/user/myproject/chart.html")
print("Chart saved to /home/user/myproject/chart.html")
