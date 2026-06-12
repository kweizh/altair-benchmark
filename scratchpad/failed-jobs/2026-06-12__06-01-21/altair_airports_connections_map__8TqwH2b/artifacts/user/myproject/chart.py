import altair as alt
from vega_datasets import data

# ── Datasets ────────────────────────────────────────────────────────────────
states_url  = data.us_10m.url
airports_url = data.airports.url
flights_url  = data.flights_airport.url

# ── Base map layer: US states ───────────────────────────────────────────────
states = alt.topo_feature(states_url, feature="states")

base = (
    alt.Chart(states)
    .mark_geoshape(fill="#f0f0f0", stroke="#ccc")
    .project(type="albersUsa")
    .properties(width=800, height=500)
)

# ── Interactive selection on origin airport ─────────────────────────────────
click_selection = alt.selection_point(
    fields=["origin"],
    on="click",
    empty=False,          # no routes drawn until a click happens
)

# ── Airport circles layer ───────────────────────────────────────────────────
airports = (
    alt.Chart(airports_url)
    .mark_circle(size=30, color="steelblue", stroke="white")
    .encode(
        latitude="latitude:Q",
        longitude="longitude:Q",
        tooltip=["iata:N", "name:N", "state:N"],
    )
    .add_params(click_selection)
)

# ── Routes (rule) layer ─────────────────────────────────────────────────────
routes = (
    alt.Chart(flights_url)
    .mark_rule(color="orange", opacity=0.5)
    .encode(
        latitude="latitude:Q",
        longitude="longitude:Q",
        latitude2="dest_lat:Q",
        longitude2="dest_lon:Q",
    )
    .transform_filter(click_selection)
    .transform_lookup(
        lookup="origin",
        from_=alt.LookupData(airports_url, key="iata", fields=["latitude", "longitude"]),
    )
    .transform_lookup(
        lookup="destination",
        from_=alt.LookupData(
            airports_url, key="iata",
            fields=["latitude", "longitude"],
        ),
        as_=["dest_lat", "dest_lon"],
    )
)

# ── Combine layers ──────────────────────────────────────────────────────────
chart = base + airports + routes

chart.save("chart.html")
print("✅ chart.html saved — open it in a browser to explore US flight routes.")
