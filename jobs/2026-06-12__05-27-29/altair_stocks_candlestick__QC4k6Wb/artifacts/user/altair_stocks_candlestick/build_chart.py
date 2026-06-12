import altair as alt
import pandas as pd

# Read the OHLCV data
df = pd.read_csv("ohlcv.csv", parse_dates=["date"])

# Define interval selection constrained to x-axis only
brush = alt.selection_interval(encodings=["x"])

# --- Upper view: candlestick chart ---
base = alt.Chart(df).encode(x=alt.X("date:T", title="Date"))

# Wick: rule from low to high
wick = base.mark_rule().encode(
    y=alt.Y("low:Q", title="Price"),
    y2=alt.Y2("high:Q"),
)

# Body: bar from open to close, colored by up/down condition
body = base.mark_bar().encode(
    y=alt.Y("open:Q"),
    y2=alt.Y2("close:Q"),
    color=alt.condition(
        alt.datum.open <= alt.datum.close,
        alt.value("green"),
        alt.value("red"),
    ),
)

# Layer wick and body, bind x-domain to brush for zoom/pan
candlestick = alt.layer(wick, body).encode(
    x=alt.X("date:T", scale=alt.Scale(domain=brush), title="Date")
)

# --- Lower view: volume bar chart ---
volume = (
    alt.Chart(df)
    .mark_bar()
    .encode(
        x=alt.X("date:T", title="Date"),
        y=alt.Y("volume:Q", title="Volume"),
        color=alt.value("steelblue"),
    )
    .add_params(brush)
    .properties(height=100)
)

# Compose with vertical concatenation
chart = candlestick & volume

# Save artifacts
chart.save("chart.html")
chart.save("chart.json")