import altair as alt
from vega_datasets import data

source = data.sp500.url

brush = alt.selection_interval(encodings=['x'])

# Lower context chart
context = alt.Chart(source).mark_area().encode(
    x='date:T',
    y='price:Q'
).properties(
    width=600,
    height=60
).add_params(
    brush
)

# Upper detail area chart
detail_area = alt.Chart(source).mark_area().encode(
    x=alt.X('date:T', scale=alt.Scale(domain=brush)),
    y='price:Q'
).properties(
    width=600,
    height=300
)

# Rule for max price in the brushed window
rule = alt.Chart(source).mark_rule(color='red').transform_filter(
    brush
).transform_aggregate(
    max_price='max(price)'
).encode(
    y='max_price:Q'
)

# Layer the detail area and the rule
detail = alt.layer(detail_area, rule)

# Concatenate the charts
chart = detail & context

chart.save('/home/user/altair_project/chart.html')
