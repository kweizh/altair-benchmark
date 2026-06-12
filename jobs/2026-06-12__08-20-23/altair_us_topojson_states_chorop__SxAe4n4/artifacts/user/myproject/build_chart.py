import altair as alt
from vega_datasets import data

# Load US state boundaries from TopoJSON
states = alt.topo_feature(data.us_10m.url, 'states')

# Build the choropleth chart
chart = alt.Chart(states).mark_geoshape().encode(
    color=alt.Color('engineers:Q', scale=alt.Scale(scheme='blues')),
    tooltip=[
        alt.Tooltip('state:N'),
        alt.Tooltip('engineers:Q')
    ]
).transform_lookup(
    lookup='id',
    from_=alt.LookupData(
        data.population_engineers_hurricanes.url,
        key='id',
        fields=['state', 'engineers']
    )
).project(
    type='albersUsa'
).properties(
    width=700,
    height=400
)

# Save as self-contained HTML
chart.save('/home/user/myproject/chart.html')