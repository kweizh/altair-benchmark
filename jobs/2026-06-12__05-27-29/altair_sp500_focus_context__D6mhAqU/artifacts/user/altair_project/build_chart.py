"""
Build the S&P 500 Focus + Context dashboard and save as chart.html.

Upper panel: filled area of price vs date, with a horizontal rule
             marking the running maximum price inside the brushed window.
Lower panel: compact area chart (navigator) with an x-only interval brush
             that controls the upper panel's x-axis domain.
"""

import altair as alt
from vega_datasets import data

# Use the URL form of the dataset (no pandas pre-processing)
source = data.sp500.url

# Interval brush restricted to the x encoding only
brush = alt.selection_interval(encodings=["x"])

# ── Upper detail chart ──────────────────────────────────────────────
detail_area = (
    alt.Chart(source)
    .mark_area()
    .encode(
        x=alt.X("date:T", scale=alt.Scale(domain=brush)),
        y="price:Q",
    )
)

# Horizontal rule marking the maximum price inside the brushed window.
# transform_filter narrows the data to the brush range first,
# then transform_aggregate computes the max price.
detail_rule = (
    alt.Chart(source)
    .mark_rule(color="red", strokeWidth=2)
    .encode(y="max_price:Q")
    .transform_filter(brush)
    .transform_aggregate(max_price="max(price)")
)

# Layer the area and the rule
detail = alt.layer(detail_area, detail_rule)

# ── Lower context chart (navigator) ─────────────────────────────────
context = (
    alt.Chart(source)
    .mark_area()
    .encode(
        x="date:T",
        y="price:Q",
    )
    .add_params(brush)
    .properties(height=60)
)

# ── Vertical concatenation ──────────────────────────────────────────
chart = detail & context

# Persist as a self-contained HTML file
chart.save("/home/user/altair_project/chart.html")