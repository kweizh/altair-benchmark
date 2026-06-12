import altair as alt
from vega_datasets import data

chart = alt.Chart(data.cars.url).mark_bar().encode(
    x=alt.X('Origin:N', sort='-y'),
    y=alt.Y('mean(Miles_per_Gallon):Q'),
    tooltip=[
        alt.Tooltip('mean(Miles_per_Gallon):Q'),
        alt.Tooltip('count():Q')
    ]
)

chart.save('/home/user/myproject/chart.html')
