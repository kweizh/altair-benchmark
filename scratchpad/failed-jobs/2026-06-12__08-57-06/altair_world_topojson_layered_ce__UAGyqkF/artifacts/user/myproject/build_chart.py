import altair as alt
import pandas as pd
from vega_datasets import data

# Build city DataFrame
cities_df = pd.DataFrame({
    'city': ['Tokyo', 'London', 'New York', 'Sao Paulo', 'Sydney'],
    'lat':  [35.6762, 51.5074, 40.7128, -23.5505, -33.8688],
    'lon':  [139.6503, -0.1278, -74.0060, -46.6333, 151.2093],
})

# TopoJSON feature for world countries
countries = alt.topo_feature(data.world_110m.url, 'countries')

# Layer 1: country geoshapes
layer_base = alt.Chart(countries).mark_geoshape(
    fill='#e8e8e8',
    stroke='white'
).project(
    type='naturalEarth1'
).properties(
    width=800,
    height=500
)

# Layer 2: city circles
layer_circles = alt.Chart(cities_df).mark_circle(
    color='red',
    size=80
).encode(
    longitude='lon:Q',
    latitude='lat:Q',
)

# Layer 3: city text labels
layer_text = alt.Chart(cities_df).mark_text(
    dy=-12
).encode(
    longitude='lon:Q',
    latitude='lat:Q',
    text='city:N',
)

# Compose layered chart
chart = alt.layer(
    layer_base,
    layer_circles,
    layer_text,
).project(
    type='naturalEarth1'
).properties(
    width=800,
    height=500
)

# Save as self-contained HTML
chart.save('/home/user/myproject/chart.html')
print("chart.html generated successfully.")
