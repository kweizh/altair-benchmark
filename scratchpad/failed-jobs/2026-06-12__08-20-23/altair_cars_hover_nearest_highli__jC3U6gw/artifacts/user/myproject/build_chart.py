import altair as alt
from vega_datasets import data

# Data source (URL-based; types declared explicitly via shorthand)
source = data.cars.url

# Hover selection: nearest point on pointer over
hover = alt.selection_point(on='pointerover', nearest=True, empty=False)

# Shared base chart
base = alt.Chart(source)

# Point layer: scatter with conditional color
points = base.mark_point().encode(
    x=alt.X('Horsepower:Q').scale(zero=False),
    y=alt.Y('Miles_per_Gallon:Q').scale(zero=False),
    color=alt.condition(hover, 'Origin:N', alt.value('lightgray'))
).add_params(hover)

# Text label layer: car Name shown above hovered point
labels = base.mark_text(dy=-10).encode(
    x=alt.X('Horsepower:Q').scale(zero=False),
    y=alt.Y('Miles_per_Gallon:Q').scale(zero=False),
    text='Name:N',
    opacity=alt.condition(hover, alt.value(1), alt.value(0))
)

# Layered chart with specified dimensions
chart = alt.layer(points, labels).properties(width=600, height=400)

# Save as self-contained HTML
chart.save('/home/user/myproject/chart.html')