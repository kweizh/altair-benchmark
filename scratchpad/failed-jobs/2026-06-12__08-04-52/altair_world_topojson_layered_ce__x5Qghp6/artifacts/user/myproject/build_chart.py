import pandas as pd
import altair as alt
from vega_datasets import data

# Create DataFrame
cities = pd.DataFrame({
    'city': ['Tokyo', 'London', 'New York', 'Sao Paulo', 'Sydney'],
    'lat': [35.6762, 51.5074, 40.7128, -23.5505, -33.8688],
    'lon': [139.6503, -0.1278, -74.0060, -46.6333, 151.2093]
})

# Get world data
world = alt.topo_feature(data.world_110m.url, 'countries')

# Layer 1: Countries
countries = alt.Chart(world).mark_geoshape(
    fill='#e8e8e8',
    stroke='white'
)

# Layer 2: Cities points
points = alt.Chart(cities).mark_circle(
    color='red',
    size=80
).encode(
    longitude='lon:Q',
    latitude='lat:Q'
)

# Layer 3: Cities text
text = alt.Chart(cities).mark_text(
    dy=-12
).encode(
    longitude='lon:Q',
    latitude='lat:Q',
    text='city:N'
)

# Combine layers and apply projection
chart = alt.layer(
    countries,
    points,
    text
).project(
    type='naturalEarth1'
).properties(
    width=800,
    height=500
)

# Save to HTML
chart.save('/home/user/myproject/chart.html')
