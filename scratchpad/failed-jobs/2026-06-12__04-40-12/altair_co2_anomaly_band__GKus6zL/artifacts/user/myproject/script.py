import altair as alt
import pandas as pd
from vega_datasets import data

source = data.iowa_electricity.url

base = alt.Chart(source).encode(
    x=alt.X('year(year):T', scale=alt.Scale(type='time'), title='Year')
)

band = base.mark_errorband(extent='iqr', interpolate='monotone').encode(
    y=alt.Y('net_generation:Q', title='Net Generation')
)

line = base.mark_line().encode(
    y='median(net_generation):Q'
)

rule = alt.Chart(source).mark_rule(strokeDash=[4, 4], color='red').encode(
    y=alt.datum(0)
)

text = alt.Chart(source).transform_timeunit(
    year_year='year(year)'
).transform_aggregate(
    median_gen='median(net_generation)',
    groupby=['year_year']
).transform_window(
    rank='rank()',
    sort=[alt.SortField('median_gen', order='descending')]
).transform_filter(
    alt.datum.rank == 1
).transform_calculate(
    label='timeFormat(datum.year_year, "%Y") + ": " + round(datum.median_gen)'
).mark_text(align='center', dy=-15).encode(
    x=alt.X('year_year:T', scale=alt.Scale(type='time')),
    y='median_gen:Q',
    text='label:N'
)

chart = alt.layer(
    band, line, rule, text
).properties(
    title=alt.TitleParams(
        text='Iowa Electricity Net Generation',
        subtitle='IQR Error Band and Median over Time'
    )
)

chart.save('/home/user/myproject/chart.html')

with open('/home/user/myproject/output.log', 'w') as f:
    f.write('Chart written: /home/user/myproject/chart.html\n')
