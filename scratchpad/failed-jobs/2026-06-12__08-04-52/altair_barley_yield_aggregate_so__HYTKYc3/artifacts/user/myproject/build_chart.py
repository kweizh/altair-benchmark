import altair as alt
from vega_datasets import data

chart = alt.Chart(data.barley.url).mark_bar().encode(
    y=alt.Y('site:N', sort=alt.EncodingSortField(field='yield', op='mean', order='descending')),
    x=alt.X('mean(yield):Q'),
    color=alt.Color('year:N'),
    yOffset=alt.YOffset('year:N')
)

chart.save('/home/user/myproject/chart.html')
