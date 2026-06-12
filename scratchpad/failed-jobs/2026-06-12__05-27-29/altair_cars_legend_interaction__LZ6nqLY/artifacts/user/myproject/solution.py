import altair as alt
from vega_datasets import data

# Load the cars dataset
source = data.cars()

# Define a single shared legend-bound selection on Origin
legend_sel = alt.selection_point(
    fields=['Origin'],
    bind='legend',
    name='legend_sel'
)

# View A — Scatter plot
scatter = alt.Chart(source).mark_point().encode(
    x='Horsepower:Q',
    y='Miles_per_Gallon:Q',
    color='Origin:N',
    opacity=alt.condition(legend_sel, alt.value(1), alt.value(0.15))
)

# View B — Stacked bar chart
bar = alt.Chart(source).mark_bar().encode(
    x='Cylinders:O',
    y='count():Q',
    color='Origin:N',
    opacity=alt.condition(legend_sel, alt.value(1), alt.value(0.15))
)

# View C — Histogram
histogram = alt.Chart(source).mark_bar().encode(
    x=alt.X('Acceleration:Q').bin(),
    y='count():Q',
    color='Origin:N',
    opacity=alt.condition(legend_sel, alt.value(1), alt.value(0.15))
)

# Compose as (A | B) & C
dashboard = (scatter | bar) & histogram

# Attach the shared selection at the top level
dashboard = dashboard.add_params(legend_sel)

# Save to HTML
dashboard.save('/home/user/myproject/chart.html')
