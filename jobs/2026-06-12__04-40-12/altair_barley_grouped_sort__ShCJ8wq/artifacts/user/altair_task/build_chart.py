import os
import altair as alt
from vega_datasets import data

os.makedirs('/home/user/altair_task/output', exist_ok=True)

source = data.barley.url

bars = alt.Chart().mark_bar().encode(
    x=alt.X('site:N', sort={'field': 'yield', 'op': 'mean', 'order': 'descending'}),
    y=alt.Y('mean(yield):Q'),
    xOffset='variety:N',
    color=alt.Color('variety:N', scale=alt.Scale(scheme='tableau10'))
)

ticks = alt.Chart().transform_aggregate(
    mean_yield='mean(yield)',
    groupby=['site', 'year']
).mark_tick(
    color='black',
    thickness=2,
    width=40
).encode(
    x=alt.X('site:N', sort={'field': 'yield', 'op': 'mean', 'order': 'descending'}),
    y=alt.Y('mean_yield:Q')
)

chart = alt.layer(bars, ticks, data=source).facet(
    facet=alt.Facet('year:O')
).properties(
    title=alt.TitleParams(
        text='Barley Yield by Site and Variety',
        subtitle='Grouped by site, colored by variety, with per-site average overlay'
    )
)

chart.save('/home/user/altair_task/output/chart.html')
