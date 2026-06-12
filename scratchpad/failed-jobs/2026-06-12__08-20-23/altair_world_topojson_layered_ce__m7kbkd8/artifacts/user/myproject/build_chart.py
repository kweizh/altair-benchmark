import altair as alt
from vega_datasets import data
import pandas as pd

# City data
cities = pd.DataFrame({
    'city': ['Tokyo', 'London', 'New York', 'Sao Paulo', 'Sydney'],
    'lat': [35.6762, 51.5074, 40.7128, -23.5505, -33.8688],
    'lon': [139.6503, -0.1278, -74.0060, -46.6333, 151.2093]
})

# Layer 1: Country shapes from TopoJSON
countries = alt.topo_feature(data.world_110m.url, 'countries')
geoshape_layer = alt.Chart(countries).mark_geoshape(
    fill='#e8e8e8',
    stroke='white'
)

# Layer 2: City markers
circle_layer = alt.Chart(cities).mark_circle(
    color='red',
    size=80
).encode(
    longitude='lon:Q',
    latitude='lat:Q'
)

# Layer 3: City labels
text_layer = alt.Chart(cities).mark_text(
    dy=-12
).encode(
    longitude='lon:Q',
    latitude='lat:Q',
    text='city:N'
)

# Compose layered chart with projection
chart = alt.layer(
    geoshape_layer,
    circle_layer,
    text_layer
).project(
    type='naturalEarth1'
).properties(
    width=800,
    height=500
)

# Save as self-contained HTML
chart.save('/home/user/myproject/chart.html')
print("Chart saved to /home/user/myproject/chart.html")