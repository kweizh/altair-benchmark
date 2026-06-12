import altair as alt
from vega_datasets import data

# Load the cars dataset
source = data.cars()

# Define the interval brush selection on both x and y channels
brush = alt.selection_interval(encodings=['x', 'y'])

# View A — Scatter plot with interval brush
scatter = alt.Chart(source).mark_point().encode(
    x='Horsepower:Q',
    y='Miles_per_Gallon:Q',
    color='Origin:N'
).add_params(brush)

# View B — Horizontal bar chart filtered by brush
bar = alt.Chart(source).mark_bar().encode(
    y='Origin:N',
    x='count():Q'
).transform_filter(brush)

# View C — 2D binned heatmap filtered by brush
heatmap = alt.Chart(source).mark_rect().encode(
    x=alt.X('Weight_in_lbs:Q').bin(),
    y=alt.Y('Acceleration:Q').bin(),
    color='count():Q'
).transform_filter(brush)

# Compose as (A | B) & C
chart = (scatter | bar) & heatmap

# Save to HTML
chart.save('/home/user/myproject/chart.html')