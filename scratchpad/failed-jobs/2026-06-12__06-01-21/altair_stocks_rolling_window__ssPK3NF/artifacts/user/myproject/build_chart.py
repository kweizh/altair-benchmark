import altair as alt

# Data source: the well-known stocks dataset
DATA_URL = "https://cdn.jsdelivr.net/npm/vega-datasets@v1.29.0/data/stocks.csv"

# Create a parameter bound to a dropdown select widget.
# This parameter filters the chart to show only one symbol at a time.
symbol_param = alt.param(
    name="symbol_selector",
    value="MSFT",
    bind=alt.binding_select(
        options=["MSFT", "AMZN", "IBM", "GOOG", "AAPL"],
        name="Symbol: ",
    ),
)

# Base chart with the filter applied.
# All layers share this filter so the dropdown controls the entire display.
base = alt.Chart(DATA_URL).transform_filter(
    "datum.symbol == symbol_selector"
)

# Layer 1: Thin raw price lines (low opacity), coloured by symbol.
raw_price = base.mark_line(opacity=0.3, strokeWidth=1).encode(
    x=alt.X("date:T", title="Date"),
    y=alt.Y("price:Q", title="Price"),
    color=alt.Color("symbol:N", title="Symbol"),
)

# Layer 2: Bold rolling-mean lines (30-trading-day centred window), coloured by symbol.
# The window transform computes mean(price) over [-15, +15] rows, grouped by symbol.
rolling_mean = (
    base.transform_window(
        window=[{"field": "price", "op": "mean", "as": "rolling_mean"}],
        frame=[-15, 15],
        groupby=["symbol"],
    )
    .mark_line(strokeWidth=3)
    .encode(
        x="date:T",
        y=alt.Y("rolling_mean:Q", title="Price"),
        color="symbol:N",
    )
)

# Layer 3: Horizontal dashed reference rules at each symbol's all-time mean price.
# The joinaggregate transform computes mean(price) grouped by symbol and attaches
# it back to every row.
alltime_mean_rule = (
    base.transform_joinaggregate(
        joinaggregate=[{"field": "price", "op": "mean", "as": "alltime_mean"}],
        groupby=["symbol"],
    )
    .mark_rule(strokeDash=[5, 5])
    .encode(
        y=alt.Y("alltime_mean:Q", title="Price"),
        color=alt.Color("symbol:N", title="Symbol"),
    )
)

# Combine all three layers.
chart = (
    alt.layer(raw_price, rolling_mean, alltime_mean_rule)
    .add_params(symbol_param)
    .interactive(bind_y=False)  # pan/zoom on x-axis only
    .properties(
        title="Multi-Company Stock Prices with Rolling Mean & All-Time Average",
    )
)

# Save to HTML.
chart.save("/home/user/myproject/chart.html")
print("Chart saved to /home/user/myproject/chart.html")
