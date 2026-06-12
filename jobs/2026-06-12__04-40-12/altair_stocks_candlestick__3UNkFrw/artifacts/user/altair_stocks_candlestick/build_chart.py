import pandas as pd
import altair as alt

# Read data
df = pd.read_csv('ohlcv.csv')
# Convert date to datetime
df['date'] = pd.to_datetime(df['date'])

# Define selection
brush = alt.selection_interval(encodings=['x'])

# Color condition for candlestick
color_condition = alt.condition(
    "datum.open <= datum.close",
    alt.value("green"),
    alt.value("red")
)

# Base chart for candlestick
base = alt.Chart(df).encode(
    x=alt.X('date:T', scale=alt.Scale(domain=brush), title='Date')
)

# Wick (rule)
rule = base.mark_rule().encode(
    y=alt.Y('low:Q', title='Price', scale=alt.Scale(zero=False)),
    y2='high:Q',
    color=color_condition
)

# Body (bar)
bar = base.mark_bar().encode(
    y='open:Q',
    y2='close:Q',
    color=color_condition
)

# Upper view
candlestick = alt.layer(rule, bar).properties(
    width=800,
    height=400,
    title='Candlestick Chart'
)

# Lower view (volume)
volume = alt.Chart(df).mark_bar().encode(
    x=alt.X('date:T', title='Date'),
    y=alt.Y('volume:Q', title='Volume'),
    color=color_condition
).properties(
    width=800,
    height=200,
    title='Volume'
).add_params(
    brush
)

# VConcat
chart = alt.vconcat(candlestick, volume)

# Save
chart.save('chart.html')
chart.save('chart.json')
