import altair as alt
from vega_datasets import data

# ── Dataset URLs ──────────────────────────────────────────────────────────────
us_topo_url      = data.us_10m.url
airports_url     = data.airports.url
flights_url      = data.flights_airport.url

# ── Interactive selection ─────────────────────────────────────────────────────
# Triggered by clicking an airport circle; empty=False means nothing is shown
# until the user clicks a point.
airport_select = alt.selection_point(
    fields=["origin"],
    on="click",
    empty=False,
)

# ── Layer 1: US states base map ───────────────────────────────────────────────
states = alt.Chart(alt.topo_feature(us_topo_url, "states")).mark_geoshape(
    fill="#dce9f5",
    stroke="#ffffff",
    strokeWidth=1,
)

# ── Layer 2: Airport circles ──────────────────────────────────────────────────
airports = (
    alt.Chart(airports_url)
    .mark_circle(color="#1a6ea8", opacity=0.7, size=30)
    .encode(
        latitude="latitude:Q",
        longitude="longitude:Q",
        tooltip=[
            alt.Tooltip("iata:N", title="IATA"),
            alt.Tooltip("name:N", title="Airport"),
            alt.Tooltip("state:N", title="State"),
        ],
    )
    .add_params(airport_select)
)

# ── Layer 3: Flight route rules ───────────────────────────────────────────────
# Start from the flights dataset, then look up coordinates for both endpoints.
routes = (
    alt.Chart(flights_url)
    # Filter rows to only the selected origin airport
    .transform_filter(airport_select)
    # Look up origin coordinates (lat/lon land directly on the row)
    .transform_lookup(
        lookup="origin",
        from_=alt.LookupData(
            data=airports_url,
            key="iata",
            fields=["latitude", "longitude"],
        ),
    )
    # Look up destination coordinates; alias to latitude2 / longitude2
    .transform_lookup(
        lookup="destination",
        from_=alt.LookupData(
            data=airports_url,
            key="iata",
            fields=["latitude", "longitude"],
        ),
        as_=["latitude2", "longitude2"],
    )
    .mark_rule(color="#e85c2b", opacity=0.6, strokeWidth=1.5)
    .encode(
        latitude="latitude:Q",
        longitude="longitude:Q",
        latitude2="latitude2:Q",
        longitude2="longitude2:Q",
    )
)

# ── Compose layers and configure projection ───────────────────────────────────
chart = (
    (states + airports + routes)
    .project(type="albersUsa")
    .properties(
        width=900,
        height=560,
        title="US Airport Flight Connections — click an airport to see its routes",
    )
    .configure_view(stroke=None)
)

# ── Save ──────────────────────────────────────────────────────────────────────
chart.save("chart.html")
print("Saved chart.html")
