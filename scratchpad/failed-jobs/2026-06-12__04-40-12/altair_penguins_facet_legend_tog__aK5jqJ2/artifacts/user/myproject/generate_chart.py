import altair as alt
from vega_datasets import data
import pandas as pd
import json

try:
    penguins = data.penguins()
except AttributeError:
    penguins = pd.read_json("https://raw.githubusercontent.com/vega/vega-datasets/master/data/penguins.json")

selection = alt.selection_point(fields=['Species'], bind='legend')

base = alt.Chart(penguins).mark_point().encode(
    x=alt.X('Beak Length (mm):Q', scale=alt.Scale(zero=False)),
    y=alt.Y('Body Mass (g):Q', scale=alt.Scale(zero=False)),
    color='Species:N',
    opacity=alt.condition(selection, alt.value(1), alt.value(0.1))
).add_params(
    selection
).facet(
    column='Island:N'
).resolve_scale(
    y='independent'
)

base.save('/home/user/myproject/chart.html')
with open('/home/user/myproject/chart.json', 'w') as f:
    f.write(base.to_json())
