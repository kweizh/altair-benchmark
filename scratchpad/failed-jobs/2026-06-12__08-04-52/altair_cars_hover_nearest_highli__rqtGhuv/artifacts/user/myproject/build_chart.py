import altair as alt
from vega_datasets import data

# Create hover selection
hover = alt.selection_point(on='pointerover', nearest=True, empty=False)

# Base chart
base = alt.Chart(data.cars.url).encode(
    x=alt.X('Horsepower:Q').scale(zero=False),
    y=alt.Y('Miles_per_Gallon:Q').scale(zero=False)
)

# Point layer
points = base.mark_point().encode(
    color=alt.condition(hover, 'Origin:N', alt.value('lightgray'))
).add_params(hover)

# Text layer
text = base.mark_text(dy=-10).encode(
    text='Name:N',
    opacity=alt.condition(hover, alt.value(1), alt.value(0))
)

# Combine layers
chart = alt.layer(points, text).properties(
    width=600,
    height=400
)

# Save chart
chart.save('/home/user/myproject/chart.html')
