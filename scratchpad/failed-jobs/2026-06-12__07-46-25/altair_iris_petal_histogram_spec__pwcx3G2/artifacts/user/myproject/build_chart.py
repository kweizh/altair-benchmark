import altair as alt
from vega_datasets import data

# Use data.iris.url as the data source
chart = alt.Chart(data.iris.url).mark_bar().encode(
    x=alt.X('petalLength:Q', bin=alt.Bin(maxbins=20)),
    y=alt.Y(aggregate='count', type='quantitative'),
    color=alt.Color('species:N')
)

# Save the resulting chart as a single self-contained HTML file
chart.save('/home/user/myproject/chart.html')
