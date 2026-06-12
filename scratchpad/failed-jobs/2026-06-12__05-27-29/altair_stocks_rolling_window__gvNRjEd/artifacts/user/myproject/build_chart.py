import altair as alt
from vega_datasets import data

source = data.stocks.url

# Dropdown parameter for symbol selection
dropdown = alt.binding_select(
    options=['MSFT', 'AMZN', 'IBM', 'GOOG', 'AAPL'],
    name='Symbol: '
)
select_symbol = alt.selection_point(
    fields=['symbol'],
    bind=dropdown,
    name='symbol_filter'
)

# Pan/zoom via interval selection bound to scales
pan_zoom = alt.selection_interval(bind='scales')

# Base chart with data and symbol filter
base = alt.Chart(source).transform_filter(select_symbol)

# Layer 1: Raw price line (thin, low opacity)
raw_line = base.mark_line(opacity=0.3, strokeWidth=1).encode(
    x='date:T',
    y='price:Q',
    color='symbol:N'
)

# Layer 2: Rolling mean line (bold, 30-day centered window)
rolling_line = base.mark_line(strokeWidth=3).encode(
    x='date:T',
    y='rolling_mean:Q',
    color='symbol:N'
).transform_window(
    rolling_mean='mean(price)',
    frame=[-15, 15],
    groupby=['symbol']
)

# Layer 3: Reference rule at all-time mean per symbol (dashed)
ref_rule = base.mark_rule(strokeDash=[5, 5]).encode(
    y='mean_price:Q',
    color='symbol:N'
).transform_joinaggregate(
    mean_price='mean(price)',
    groupby=['symbol']
)

# Combine layers and add interactivity
chart = alt.layer(raw_line, rolling_line, ref_rule).add_params(
    select_symbol, pan_zoom
)

# Save to HTML
chart.save('/home/user/myproject/chart.html')
print("Chart saved to /home/user/myproject/chart.html")