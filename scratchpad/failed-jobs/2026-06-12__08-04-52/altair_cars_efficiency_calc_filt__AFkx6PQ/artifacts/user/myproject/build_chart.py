import altair as alt
from vega_datasets import data

# Data source
source = data.cars.url

# Create chart
chart = alt.Chart(source).transform_calculate(
    Efficiency='datum.Miles_per_Gallon / datum.Weight_in_lbs'
).transform_filter(
    alt.datum.Efficiency > 0.01
).mark_bar().encode(
    x=alt.X('Cylinders:O', sort='ascending'),
    y=alt.Y('mean(Efficiency):Q', title='Mean Efficiency (mpg/lb)'),
    color=alt.Color('Cylinders:O', scale=alt.Scale(scheme='category10'))
)

# Save chart
chart.save('/home/user/myproject/chart.html')
