import altair as alt
from vega_datasets import data

source = data.iris.url

# Create the dropdown binding
dropdown = alt.binding_select(
    options=['setosa', 'versicolor', 'virginica'],
    name='Species: '
)

# Create the parameter bound to the dropdown
species_param = alt.param(
    name='species_selection',
    value='setosa',
    bind=dropdown
)

# Build the chart
chart = alt.Chart(source).mark_circle(size=60).encode(
    x='sepalLength:Q',
    y='sepalWidth:Q',
    color=alt.when(alt.datum.species == species_param)
        .then(alt.Color('species:N'))
        .otherwise(alt.value('lightgray'))
).add_params(
    species_param
)

# Save the chart
chart.save('/home/user/myproject/chart.html')
