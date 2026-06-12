import altair as alt
import pandas as pd
from vega_datasets import data

# ── 1. World country shapes from the bundled TopoJSON ──────────────────────
countries = alt.topo_feature(data.world_110m.url, "countries")

layer_map = (
    alt.Chart(countries)
    .mark_geoshape(fill="#e8e8e8", stroke="white")
)

# ── 2. City coordinates ────────────────────────────────────────────────────
cities_df = pd.DataFrame(
    {
        "city": ["Tokyo", "London", "New York", "Sao Paulo", "Sydney"],
        "lat":  [35.6762,  51.5074,   40.7128,   -23.5505,  -33.8688],
        "lon":  [139.6503,  -0.1278,  -74.0060,   -46.6333,  151.2093],
    }
)

# ── 3. Red circle markers ──────────────────────────────────────────────────
layer_circles = (
    alt.Chart(cities_df)
    .mark_circle(color="red", size=80)
    .encode(
        longitude=alt.Longitude("lon:Q"),
        latitude=alt.Latitude("lat:Q"),
    )
)

# ── 4. City-name text labels (offset 12 px above the circle) ──────────────
layer_labels = (
    alt.Chart(cities_df)
    .mark_text(dy=-12)
    .encode(
        longitude=alt.Longitude("lon:Q"),
        latitude=alt.Latitude("lat:Q"),
        text=alt.Text("city:N"),
    )
)

# ── 5. Compose and configure ───────────────────────────────────────────────
chart = (
    alt.layer(layer_map, layer_circles, layer_labels)
    .project("naturalEarth1")
    .properties(width=800, height=500)
)

# ── 6. Export to a self-contained HTML file ────────────────────────────────
chart.save("chart.html")
print("chart.html written successfully.")
