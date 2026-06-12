import altair as alt
from vega_datasets import data

source = data.seattle_weather.url

domain = ['sun', 'fog', 'drizzle', 'rain', 'snow']
range_ = ['#e7ba52', '#c7c7c7', '#aec7e8', '#1f77b4', '#9467bd']

chart = alt.Chart(source).mark_bar().encode(
    y='weather:N',
    x='count():Q',
    color=alt.Color('weather:N', scale=alt.Scale(domain=domain, range=range_))
)

chart.save('chart.html')
