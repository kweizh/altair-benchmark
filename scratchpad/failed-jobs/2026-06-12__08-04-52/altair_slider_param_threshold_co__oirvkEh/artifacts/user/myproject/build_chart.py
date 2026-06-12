import altair as alt
from vega_datasets import data

source = data.cars.url

slider = alt.binding_range(min=50, max=250, step=10, name='HP threshold: ')
hp_threshold = alt.param(value=150, bind=slider, name='hp_threshold')

color = alt.when(alt.datum.Horsepower < hp_threshold).then(
    alt.value('steelblue')
).otherwise(
    alt.value('orange')
)

chart = alt.Chart(source).mark_point().encode(
    x='Horsepower:Q',
    y='Miles_per_Gallon:Q',
    color=color
).properties(
    title='MPG vs Horsepower (threshold)'
).add_params(
    hp_threshold
)

chart.save('/home/user/myproject/chart.html')
