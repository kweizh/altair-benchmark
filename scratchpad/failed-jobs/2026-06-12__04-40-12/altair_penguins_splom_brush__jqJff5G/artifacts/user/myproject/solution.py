import altair as alt
from vega_datasets import data

try:
    source = data.penguins.url
except AttributeError:
    source = 'https://cdn.jsdelivr.net/npm/vega-datasets@v1.29.0/data/penguins.json'

features = [
    'Beak Length (mm)',
    'Beak Depth (mm)',
    'Flipper Length (mm)',
    'Body Mass (g)'
]

brush = alt.selection_interval(encodings=['x', 'y'])

chart = alt.Chart(source).mark_point().encode(
    x=alt.X(alt.repeat('column'), type='quantitative', scale=alt.Scale(zero=False)),
    y=alt.Y(alt.repeat('row'), type='quantitative', scale=alt.Scale(zero=False)),
    color=alt.condition(brush, 'Species:N', alt.value('lightgray'))
).properties(
    width=150,
    height=150
).add_params(
    brush
).repeat(
    row=features,
    column=features
)

chart.save('/home/user/myproject/chart.html')
