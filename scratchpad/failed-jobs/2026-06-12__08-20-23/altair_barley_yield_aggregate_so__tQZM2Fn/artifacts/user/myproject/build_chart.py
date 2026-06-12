import altair as alt
from vega_datasets import data

# Load the barley dataset via URL
source = data.barley.url

# Build a horizontal grouped bar chart
chart = alt.Chart(source).mark_bar().encode(
    y=alt.Y('site:N', sort={'field': 'yield', 'op': 'mean', 'order': 'descending'}),
    x=alt.X('mean(yield):Q'),
    color=alt.Color('year:N'),
    yOffset=alt.YOffset('year:N')
)

# Save as self-contained HTML
chart.save('/home/user/myproject/chart.html')