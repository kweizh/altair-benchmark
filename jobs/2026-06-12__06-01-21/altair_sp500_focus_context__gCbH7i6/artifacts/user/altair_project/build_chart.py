import altair as alt
from vega_datasets import data

# ── Shared data source ──────────────────────────────────────────────────────
source = data.sp500.url

# ── Brush (interval selection, x-only) ─────────────────────────────────────
brush = alt.selection_interval(encodings=["x"], name="brush")

# ── Base area chart (used by both panels) ──────────────────────────────────
base = (
    alt.Chart(source)
    .mark_area()
    .encode(
        x=alt.X("date:T", title=None),
        y=alt.Y("price:Q", title=None),
    )
)

# ── Upper detail chart ─────────────────────────────────────────────────────
#   The detail panel is a layer of:
#     1. The filled area, whose x-domain is driven by the brush.
#     2. A horizontal rule showing the running max price inside the brush window.

detail_area = base.encode(
    x=alt.X("date:T", title=None, scale=alt.Scale(domain={"param": "brush"})),
    y=alt.Y("price:Q", title="Price"),
)

# Running maximum annotation: filter to brushed range, compute max price,
# then draw a horizontal rule at that y value.
max_rule = (
    alt.Chart(source)
    .mark_rule(color="red", strokeWidth=2)
    .encode(y=alt.Y("max_price:Q"))
    .transform_filter(brush)
    .transform_aggregate(max_price="max(price)")
)

detail = detail_area + max_rule

# ── Lower context (navigator) chart ────────────────────────────────────────
context = base.properties(height=60).add_params(brush)

# ── Concatenate & save ─────────────────────────────────────────────────────
chart = detail & context

chart.save("/home/user/altair_project/chart.html")
print("✔ chart.html generated")
