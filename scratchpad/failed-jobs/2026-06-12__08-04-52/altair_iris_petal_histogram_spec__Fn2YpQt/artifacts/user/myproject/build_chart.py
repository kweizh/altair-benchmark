import altair as alt
from vega_datasets import data

chart = alt.Chart(data.iris.url).mark_bar().encode(
    x=alt.X('petalLength:Q', bin=alt.Bin(maxbins=20)),
    y='count()',
    color='species:N'
)

chart.save('/home/user/myproject/chart.html')
