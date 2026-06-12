import altair as alt
from vega_datasets import data

# Load dataset URLs
airports_url = data.airports.url
flights_url = data.flights_airport.url
states_url = data.us_10m.url

# Base US states map layer (geographic background)
states = alt.topo_feature(states_url, 'states')
background = alt.Chart(states).mark_geoshape(
    fill='lightgray',
    stroke='white'
).properties(
    width=800,
    height=500
)

# Interactive point selection triggered by clicking an airport circle
select_origin = alt.selection_point(
    name='select_origin',
    fields=['origin'],
    on='click',
    empty=False
)

# Airport circles layer
airports = alt.Chart(airports_url).transform_calculate(
    origin="datum.iata"
).mark_circle(
    size=15,
    color='steelblue',
    opacity=0.8
).encode(
    latitude='latitude:Q',
    longitude='longitude:Q',
    tooltip=['origin:N', 'name:N', 'city:N', 'state:N']
).add_params(
    select_origin
)

# Flight routes layer (rule segments)
routes = alt.Chart(flights_url).mark_rule(
    color='orange',
    strokeWidth=1.5,
    opacity=0.8
).encode(
    latitude='latitude:Q',
    longitude='longitude:Q',
    latitude2='latitude2:Q',
    longitude2='longitude2:Q'
).transform_lookup(
    lookup='origin',
    from_=alt.LookupData(airports_url, key='iata', fields=['latitude', 'longitude'])
).transform_lookup(
    lookup='destination',
    from_=alt.LookupData(airports_url, key='iata', fields=['latitude', 'longitude']),
    as_=['latitude2', 'longitude2']
).transform_filter(
    select_origin
)

# Combine the layers with albersUsa projection
chart = (background + routes + airports).project('albersUsa')

# Save the chart
chart.save('chart.html')
