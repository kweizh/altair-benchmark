import altair as alt
from vega_datasets import data

if not hasattr(data, 'penguins'):
    class _Penguins:
        url = 'https://cdn.jsdelivr.net/npm/vega-datasets@v1.29.0/data/penguins.json'
    data.penguins = _Penguins()

base = alt.Chart(data.penguins.url).mark_point().encode(
    x=alt.X(alt.repeat('column'), type='quantitative', scale=alt.Scale(zero=False)),
    y=alt.Y(alt.repeat('row'), type='quantitative', scale=alt.Scale(zero=False)),
    color='Species:N'
).properties(
    width=180,
    height=180
)

chart = base.repeat(
    row=['Body Mass (g)', 'Flipper Length (mm)'],
    column=['Beak Length (mm)', 'Beak Depth (mm)']
)

chart.save('chart.html')
