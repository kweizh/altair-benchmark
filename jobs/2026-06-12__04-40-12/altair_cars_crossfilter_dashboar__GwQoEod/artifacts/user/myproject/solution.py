import altair as alt
from vega_datasets import data

cars = data.cars.url

brush = alt.selection_interval(encodings=['x', 'y'])

A = alt.Chart(cars).mark_point().encode(
    x='Horsepower:Q',
    y='Miles_per_Gallon:Q',
    color='Origin:N'
).add_params(
    brush
)

B = alt.Chart(cars).mark_bar().encode(
    y='Origin:N',
    x='count():Q'
).transform_filter(
    brush
)

C = alt.Chart(cars).mark_rect().encode(
    x=alt.X('Weight_in_lbs:Q').bin(),
    y=alt.Y('Acceleration:Q').bin(),
    color='count():Q'
).transform_filter(
    brush
)

chart = (A | B) & C

chart.save('/home/user/myproject/chart.html')
