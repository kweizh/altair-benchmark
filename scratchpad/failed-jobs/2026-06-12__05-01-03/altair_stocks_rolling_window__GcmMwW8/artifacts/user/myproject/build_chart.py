"""
Multi-company stock chart with Vega-Altair.

Layers:
  1. Thin raw price line per symbol (low opacity).
  2. Bold 30-day centred rolling-mean line per symbol (window transform, frame [-15, 15]).
  3. Horizontal dashed reference rule at per-symbol all-time mean (joinaggregate transform).

Interactivity:
  - Dropdown widget that filters to a single symbol.
  - Pan / zoom on the x-axis (interval selection bound to scales).

All reshaping is performed inside the Vega-Lite spec; the data source is the
canonical vega-datasets stocks CSV URL.
"""

import altair as alt
from vega_datasets import data

# ---------------------------------------------------------------------------
# Data source – URL only, no pandas pre-processing
# ---------------------------------------------------------------------------
stocks_url = data.stocks.url   # https://cdn.jsdelivr.net/npm/vega-datasets@.../stocks.csv

source = alt.UrlData(url=stocks_url, format=alt.CsvDataFormat())

TICKERS = ["MSFT", "AMZN", "IBM", "GOOG", "AAPL"]

# ---------------------------------------------------------------------------
# Parameters
# ---------------------------------------------------------------------------

# 1. Dropdown filter parameter
symbol_param = alt.param(
    name="symbol_selection",
    bind=alt.binding_select(
        options=TICKERS,
        name="Symbol: ",
    ),
    value="MSFT",  # default selection
)

# 2. Pan/zoom on x-axis — interval selection bound to scales
# Using alt.selection_interval with bind="scales" restricts the interval to
# the x-axis only, giving the standard pan/zoom behaviour on that axis.
zoom_param = alt.selection_interval(
    bind="scales",
    encodings=["x"],
    name="grid",
)

# ---------------------------------------------------------------------------
# Shared colour encoding (symbol → colour)
# ---------------------------------------------------------------------------
color_enc = alt.Color("symbol:N", legend=alt.Legend(title="Symbol"))

# ---------------------------------------------------------------------------
# Layer 1 – Raw price line (thin, low opacity)
# ---------------------------------------------------------------------------
raw_line = (
    alt.Chart(source)
    .mark_line(opacity=0.25, strokeWidth=1)
    .encode(
        x=alt.X("date:T", title="Date"),
        y=alt.Y("price:Q", title="Price (USD)"),
        color=color_enc,
        tooltip=[
            alt.Tooltip("date:T", title="Date", format="%Y-%m-%d"),
            alt.Tooltip("symbol:N", title="Symbol"),
            alt.Tooltip("price:Q", title="Price", format=".2f"),
        ],
    )
)

# ---------------------------------------------------------------------------
# Layer 2 – Rolling-mean line (30-day centred window, bold)
#
# transform_window parameters:
#   window   : [{"op": "mean", "field": "price", "as": "rolling_mean"}]
#   frame    : [-15, 15]  → 15 days before + current + 15 days after = 31 rows
#              (Vega-Lite's window frame is inclusive on both sides)
#   groupby  : ["symbol"]
#   sort     : [{"field": "date", "order": "ascending"}]
# ---------------------------------------------------------------------------
rolling_line = (
    alt.Chart(source)
    .transform_window(
        rolling_mean="mean(price)",
        frame=[-15, 15],
        groupby=["symbol"],
        sort=[alt.SortField("date", order="ascending")],
    )
    .mark_line(strokeWidth=2.5)
    .encode(
        x=alt.X("date:T"),
        y=alt.Y("rolling_mean:Q", title="Price (USD)"),
        color=color_enc,
        tooltip=[
            alt.Tooltip("date:T", title="Date", format="%Y-%m-%d"),
            alt.Tooltip("symbol:N", title="Symbol"),
            alt.Tooltip("rolling_mean:Q", title="30-day mean", format=".2f"),
        ],
    )
)

# ---------------------------------------------------------------------------
# Layer 3 – Horizontal dashed reference rule at per-symbol all-time mean
#
# transform_joinaggregate attaches the aggregate back onto every matching row,
# so the rule mark can use it directly as a y encoding.
# ---------------------------------------------------------------------------
mean_rule = (
    alt.Chart(source)
    .transform_joinaggregate(
        mean_price="mean(price)",
        groupby=["symbol"],
    )
    .mark_rule(strokeDash=[6, 3], strokeWidth=1.5, opacity=0.8)
    .encode(
        y=alt.Y("mean_price:Q", title="All-time mean"),
        color=color_enc,
        tooltip=[
            alt.Tooltip("symbol:N", title="Symbol"),
            alt.Tooltip("mean_price:Q", title="All-time mean", format=".2f"),
        ],
    )
)

# ---------------------------------------------------------------------------
# Compose the layered chart
# ---------------------------------------------------------------------------
chart = (
    alt.layer(raw_line, rolling_line, mean_rule)
    .add_params(symbol_param, zoom_param)
    # Filter every layer to the selected symbol.
    # A plain string is treated as a Vega expression test predicate in Altair 6;
    # "symbol_selection" matches the param name defined above.
    .transform_filter("datum.symbol === symbol_selection")
    .properties(
        title="Multi-Company Stock Prices",
        width=900,
        height=450,
    )
    .resolve_scale(color="shared")
)

# ---------------------------------------------------------------------------
# Save
# ---------------------------------------------------------------------------
out_path = "/home/user/myproject/chart.html"
chart.save(out_path)
print(f"Chart saved to {out_path}")
