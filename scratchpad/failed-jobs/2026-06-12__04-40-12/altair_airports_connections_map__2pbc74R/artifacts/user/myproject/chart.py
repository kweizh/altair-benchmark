import altair as alt
from vega_datasets import data

states = alt.topo_feature(data.us_10m.url, feature='states')
airports = data.airports.url
flights = data.flights_airport.url

# Base map
background = alt.Chart(states).mark_geoshape(
    fill='lightgray',
    stroke='white'
)

# Selection
select_origin = alt.selection_point(
    fields=['origin'],
    on='click',
    empty=False
)

# Airports layer
airports_layer = alt.Chart(airports).transform_calculate(
    origin="datum.iata"
).mark_circle(
    size=50,
    color='steelblue',
    opacity=0.8
).encode(
    longitude='longitude:Q',
    latitude='latitude:Q',
    tooltip=['origin:N', 'name:N', 'city:N', 'state:N']
).add_params(
    select_origin
)

# Flights layer
flights_layer = alt.Chart(flights).mark_rule(
    color='black',
    opacity=0.35
).transform_filter(
    select_origin
).transform_lookup(
    lookup='origin',
    from_=alt.LookupData(airports, 'iata', ['latitude', 'longitude'])
).transform_lookup(
    lookup='destination',
    from_=alt.LookupData(airports, 'iata', ['latitude', 'longitude']),
    as_=['latitude2', 'longitude2']
).encode(
    longitude='longitude:Q',
    latitude='latitude:Q',
    longitude2='longitude2:Q',
    latitude2='latitude2:Q'
)

# Combine layers and apply projection to the whole chart
chart = (background + flights_layer + airports_layer).project(
    'albersUsa'
).properties(
    width=800,
    height=500
)

chart.save('chart.html')
