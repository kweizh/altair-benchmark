import altair as alt
from vega_datasets import data

# ── Datasets ──────────────────────────────────────────────────────────
states = alt.topo_feature(data.us_10m.url, "states")
airports_url = data.airports.url
flights_url = data.flights_airport.url

# ── Projection ────────────────────────────────────────────────────────
projection = alt.Projection(type="albersUsa")

# ── 1. Base layer: US states ──────────────────────────────────────────
base = (
    alt.Chart(states, projection=projection)
    .mark_geoshape(fill="lightgray", stroke="white")
)

# ── 2. Airport circles ────────────────────────────────────────────────
# Point selection triggered by clicking a circle
airport_selector = alt.selection_point(
    fields=["origin"], on="click", empty=False
)

airports = (
    alt.Chart(airports_url, projection=projection)
    .mark_circle(size=40, color="steelblue")
    .encode(
        latitude="latitude:Q",
        longitude="longitude:Q",
        tooltip=["iata:N", "name:N"],
    )
    .add_params(airport_selector)
)

# ── 3. Route layer: rule marks from origin to destination ─────────────
routes = (
    alt.Chart(flights_url, projection=projection)
    .mark_rule(color="firebrick", strokeWidth=1)
    .transform_filter(airport_selector)
    .transform_lookup(
        lookup="origin",
        from_=alt.LookupData(airports_url, "iata", ["latitude", "longitude"]),
    )
    .transform_lookup(
        lookup="destination",
        from_=alt.LookupData(airports_url, "iata", ["latitude", "longitude"]),
        as_=["dest_lat", "dest_lon"],
    )
    .encode(
        latitude="latitude:Q",
        longitude="longitude:Q",
        latitude2="dest_lat:Q",
        longitude2="dest_lon:Q",
    )
)

# ── Combine layers ────────────────────────────────────────────────────
chart = base + airports + routes

chart.save("chart.html")
print("Saved chart.html")