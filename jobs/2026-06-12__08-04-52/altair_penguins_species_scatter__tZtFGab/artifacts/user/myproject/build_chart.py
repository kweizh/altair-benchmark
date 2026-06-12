import altair as alt
from vega_datasets import data

source = data.penguins.url

chart = alt.Chart(source).mark_point(
    filled=True,
    size=80
).encode(
    x=alt.X('Flipper Length (mm):Q', scale=alt.Scale(zero=False)),
    y=alt.Y('Body Mass (g):Q', scale=alt.Scale(zero=False)),
    color='Species:N',
    shape='Sex:N',
    tooltip=[
        'Species:N',
        'Island:N',
        'Flipper Length (mm):Q',
        'Body Mass (g):Q'
    ]
).interactive()

chart.save('/home/user/myproject/chart.html')
