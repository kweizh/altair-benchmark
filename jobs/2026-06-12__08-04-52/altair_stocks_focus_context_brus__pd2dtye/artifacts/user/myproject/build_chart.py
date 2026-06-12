import altair as alt
from vega_datasets import data

# Create a selection that chooses the nearest point & selects based on x-value
brush = alt.selection_interval(encodings=['x'])

# Base chart
base = alt.Chart(data.sp500.url).mark_area().encode(
    x='date:T',
    y='price:Q'
)

# Upper detail view
upper = base.encode(
    alt.X('date:T', scale=alt.Scale(domain=brush))
).properties(
    width=600,
    height=250
)

# Lower overview view
lower = base.properties(
    width=600,
    height=70
).add_params(
    brush
)

# Concatenate the two views
chart = upper & lower

# Save the chart to an HTML file
chart.save('chart.html')
