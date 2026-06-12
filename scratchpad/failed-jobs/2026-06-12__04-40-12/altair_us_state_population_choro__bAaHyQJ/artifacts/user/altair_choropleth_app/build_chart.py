import altair as alt
from vega_datasets import data

# Datasets
states = alt.topo_feature(data.us_10m.url, 'states')
pop_eng_hur = data.population_engineers_hurricanes.url

# Dropdown parameter
metrics = ['population', 'engineers', 'hurricanes']
metric_select = alt.binding_select(options=metrics, name='Select Metric: ')
metric_param = alt.param(name='metric', value='population', bind=metric_select)

# Chart
chart = alt.Chart(states).mark_geoshape(
    stroke='white'
).transform_lookup(
    lookup='id',
    from_=alt.LookupData(pop_eng_hur, 'id', ['state', 'population', 'engineers', 'hurricanes'])
).transform_calculate(
    current_metric_value="datum[metric]"
).encode(
    color=alt.Color('current_metric_value:Q', title='Value'),
    tooltip=[
        alt.Tooltip('state:N', title='State'),
        alt.Tooltip('current_metric_value:Q', title='Value')
    ]
).add_params(
    metric_param
).project(
    type='albersUsa'
).properties(
    width=800,
    height=500,
    title='US State Choropleth'
)

chart.save('/home/user/altair_choropleth_app/chart.html')
