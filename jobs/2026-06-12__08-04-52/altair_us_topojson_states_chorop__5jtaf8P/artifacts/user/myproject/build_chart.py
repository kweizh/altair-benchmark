import altair as alt
from vega_datasets import data

# Load TopoJSON data for US states
states = alt.topo_feature(data.us_10m.url, 'states')

# Load population data URL
pop_data_url = data.population_engineers_hurricanes.url

# Create the chart
chart = alt.Chart(states).mark_geoshape().transform_lookup(
    lookup='id',
    from_=alt.LookupData(pop_data_url, key='id', fields=['state', 'engineers'])
).encode(
    color=alt.Color('engineers:Q', scale=alt.Scale(scheme='blues')),
    tooltip=['state:N', 'engineers:Q']
).project(
    type='albersUsa'
).properties(
    width=700,
    height=400
)

# Save the chart as an HTML file
chart.save('/home/user/myproject/chart.html')
