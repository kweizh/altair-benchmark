import altair as alt
from vega_datasets import data
import os

# Load data
cars = data.cars.url

# Define the shared selection
selection = alt.selection_point(name='origin_select', fields=['Origin'], bind='legend')

# View A: Scatter plot
view_a = alt.Chart(cars).mark_point().encode(
    x='Horsepower:Q',
    y='Miles_per_Gallon:Q',
    color='Origin:N',
    opacity=alt.condition(selection, alt.value(1), alt.value(0.15))
)

# View B: Stacked bar chart
view_b = alt.Chart(cars).mark_bar().encode(
    x='Cylinders:O',
    y='count()',
    color='Origin:N',
    opacity=alt.condition(selection, alt.value(1), alt.value(0.15))
)

# View C: Histogram
view_c = alt.Chart(cars).mark_bar().encode(
    x=alt.X('Acceleration:Q', bin=True),
    y='count()',
    color='Origin:N',
    opacity=alt.condition(selection, alt.value(1), alt.value(0.15))
)

# Compose the charts
dashboard = ((view_a | view_b) & view_c).add_params(
    selection
)

# Save the chart
os.makedirs('/home/user/myproject', exist_ok=True)
dashboard.save('/home/user/myproject/chart.html')
