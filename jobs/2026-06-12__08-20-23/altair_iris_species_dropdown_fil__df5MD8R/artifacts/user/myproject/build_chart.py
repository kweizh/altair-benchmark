import altair as alt
from vega_datasets import data

# Load iris data from URL (requires explicit type shorthands)
source = data.iris.url

# Define a bound dropdown parameter for species selection
dropdown = alt.binding_select(
    options=['setosa', 'versicolor', 'virginica'],
    name='Species: '
)
species_param = alt.param(
    value='setosa',
    bind=dropdown
)

# Build the scatter plot with conditional colouring
chart = alt.Chart(source).mark_point().encode(
    x=alt.X('sepalLength:Q'),
    y=alt.Y('sepalWidth:Q'),
    color=alt.when(species_param == alt.datum.species)
        .then(alt.Color('species:N'))
        .otherwise(alt.value('lightgray'))
).add_params(species_param)

# Save as a single self-contained HTML file
chart.save('/home/user/myproject/chart.html')