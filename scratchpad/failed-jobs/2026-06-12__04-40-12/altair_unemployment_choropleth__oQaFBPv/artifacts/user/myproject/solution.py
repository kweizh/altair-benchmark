import altair as alt
from vega_datasets import data

counties = alt.topo_feature(data.us_10m.url, 'counties')
source = data.unemployment.url

brush = alt.selection_interval(encodings=['x'])

map_chart = alt.Chart(counties).mark_geoshape().project(
    type='albersUsa'
).transform_lookup(
    lookup='id',
    from_=alt.LookupData(source, 'id', ['rate'])
).encode(
    color=alt.Color('rate:Q', scale=alt.Scale(type='threshold', domain=[0.02, 0.04, 0.06, 0.08], scheme='blues')),
    tooltip=['id:N', 'rate:Q']
).transform_filter(
    brush
).properties(
    width=600,
    height=400
)

hist_chart = alt.Chart(source).mark_bar().encode(
    x=alt.X('rate:Q', bin=True),
    y='count()'
).add_params(
    brush
).properties(
    width=600,
    height=200
)

dashboard = alt.vconcat(map_chart, hist_chart)
dashboard.save('/home/user/myproject/chart.html')
