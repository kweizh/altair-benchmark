import altair as alt
from vega_datasets import data

# Create the interval brush selection limited to the x-axis
brush = alt.selection_interval(encodings=['x'])

# Base chart using URL-based data source with explicit type shorthands
base = alt.Chart(data.sp500.url).mark_area().encode(
    x='date:T',
    y='price:Q'
)

# Upper detail (focus) view:
# - Override x encoding so its scale domain is bound to the brush selection
# - Width 600, height 250
detail = base.encode(
    x=alt.X('date:T', scale=alt.Scale(domain={'param': brush.name}))
).properties(
    width=600,
    height=250
)

# Lower overview (context) view:
# - Attach the brush selection so the user can drag an interval
# - Width 600, height 70
overview = base.add_params(
    brush
).properties(
    width=600,
    height=70
)

# Vertically concatenate: detail on top, overview on bottom
chart = alt.vconcat(detail, overview)

# Save as self-contained HTML
chart.save('/home/user/myproject/chart.html')