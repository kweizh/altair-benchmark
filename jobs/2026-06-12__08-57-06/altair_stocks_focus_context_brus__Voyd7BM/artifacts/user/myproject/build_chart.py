import altair as alt
from vega_datasets import data

# ── data source (URL-based, explicit types) ──────────────────────────
source = data.sp500.url

# ── shared base chart ────────────────────────────────────────────────
base = (
    alt.Chart(source)
    .mark_area()
    .encode(
        alt.X("date:T", title=None),
        alt.Y("price:Q", title=None),
    )
    .properties(width=600)
)

# ── interval brush (constrained to the x / time axis) ────────────────
brush = alt.selection_interval(encodings=["x"], name="brush")

# ── upper / detail (focus) view ──────────────────────────────────────
detail = base.encode(
    alt.X("date:T", title=None, scale=alt.Scale(domain=brush))
).properties(height=250)

# ── lower / overview (context) view ──────────────────────────────────
context = base.properties(height=70).add_params(brush)

# ── vertical concatenation ───────────────────────────────────────────
chart = alt.vconcat(detail, context)

# ── save self-contained HTML ─────────────────────────────────────────
chart.save("chart.html")
print("✅ chart.html written")
