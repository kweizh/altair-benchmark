import altair as alt
import json
from vega_datasets import data

# Load the penguins dataset
df = data.penguins()

# Create a point selection projected over the 'Species' field and bound to the chart's legend
selection = alt.selection_point(
    name='species_select',
    fields=['Species'],
    bind='legend'
)

# Build the base scatter plot
base_chart = alt.Chart(df).mark_point().encode(
    x=alt.X('Beak Length (mm):Q', scale=alt.Scale(zero=False)),
    y=alt.Y('Body Mass (g):Q', scale=alt.Scale(zero=False)),
    color='Species:N',
    opacity=alt.condition(selection, alt.value(1.0), alt.value(0.1))
).add_params(
    selection
)

# Create the faceted chart
faceted_chart = base_chart.facet(
    column='Island:N'
).resolve_scale(
    y='independent'
)

# Save the standalone HTML produced by Altair
faceted_chart.save('/home/user/myproject/chart.html')

# Save the exact Vega-Lite specification emitted by Altair
# Use to_json() or to_dict() as instructed
chart_json = faceted_chart.to_json()
with open('/home/user/myproject/chart.json', 'w') as f:
    f.write(chart_json)

print("Chart HTML and JSON successfully generated!")
