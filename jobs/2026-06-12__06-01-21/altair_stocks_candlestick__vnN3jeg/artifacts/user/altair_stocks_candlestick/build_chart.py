import altair as alt
import pandas as pd

# ---------------------------------------------------------------------------
# 1. Load the OHLCV dataset
# ---------------------------------------------------------------------------
df = pd.read_csv("ohlcv.csv", parse_dates=["date"])

# ---------------------------------------------------------------------------
# 2. Shared brush selection – constrained to the x (date) axis only
# ---------------------------------------------------------------------------
brush = alt.selection_interval(encodings=["x"])

# ---------------------------------------------------------------------------
# 3. Upper view – candlestick (wick + body)
# ---------------------------------------------------------------------------
# Common date encoding shared by both layers
x_base = alt.X("date:T", title=None)

# --- Wick layer (rule): low → high ---
wick = (
    alt.Chart(df)
    .mark_rule()
    .encode(
        x=x_base,
        y=alt.Y("low:Q", title="Price", scale=alt.Scale(zero=False)),
        y2=alt.Y2("high:Q"),
    )
)

# --- Body layer (bar): open → close, colored by up/down day ---
color_condition = alt.condition(
    "datum.open <= datum.close",
    alt.value("#26a69a"),   # green for up days
    alt.value("#ef5350"),   # red for down days
)

body = (
    alt.Chart(df)
    .mark_bar()
    .encode(
        x=x_base,
        y=alt.Y("open:Q", title="Price", scale=alt.Scale(zero=False)),
        y2=alt.Y2("close:Q"),
        color=color_condition,
    )
)

# Layer wick + body, then bind the x-domain to the brush
candlestick = (
    (wick + body)
    .encode(
        x=alt.X("date:T", title=None, scale=alt.Scale(domain=brush)),
    )
)

# ---------------------------------------------------------------------------
# 4. Lower view – volume bars
# ---------------------------------------------------------------------------
volume_chart = (
    alt.Chart(df)
    .mark_bar()
    .encode(
        x=alt.X("date:T", title="Date"),
        y=alt.Y("volume:Q", title="Volume"),
        color=alt.value("#607d8b"),
    )
    .add_params(brush)
)

# ---------------------------------------------------------------------------
# 5. Vertically concatenate
# ---------------------------------------------------------------------------
chart = alt.vconcat(candlestick, volume_chart).resolve_scale(x="shared")

# ---------------------------------------------------------------------------
# 6. Persist artifacts
# ---------------------------------------------------------------------------
chart.save("chart.html")
chart.save("chart.json")
