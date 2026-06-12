import altair as alt
from altair.utils.html import spec_to_html
from vega_datasets import data

# URL-based data source
source = data.sp500.url

# Single interval brush selection limited to the x (time) axis
brush = alt.selection_interval(encodings=["x"])

# Shared base chart
base = alt.Chart(source).mark_area().encode(
    x="date:T",
    y="price:Q",
)

# Upper detail (focus) view – x-scale domain is bound to the brush
focus = base.encode(
    x=alt.X("date:T", scale=alt.Scale(domain=brush)),
    y="price:Q",
).properties(width=600, height=250)

# Lower overview (context) view – add_params attaches the brush
context = base.encode(
    x="date:T",
    y="price:Q",
).properties(width=600, height=70).add_params(brush)

# Vertically concatenate: focus on top, context on bottom
chart = alt.vconcat(focus, context)

# ── Altair 6 hoists add_params to the top-level vconcat spec with a `views`
# bookkeeping key.  Re-seat the brush param inside vconcat[1].params so the
# embedded spec satisfies the acceptance criteria (brush lives on context view).
spec = chart.to_dict()           # serialise ONCE; all mutations happen here
brush_name = brush.name

top_params = spec.get("params", [])
interval_params = [
    {k: v for k, v in p.items() if k != "views"}   # drop the `views` key
    for p in top_params
    if isinstance(p.get("select"), dict)
    and p["select"].get("type") == "interval"
    and p.get("name") == brush_name
]
other_params = [
    p for p in top_params
    if not (isinstance(p.get("select"), dict)
            and p["select"].get("type") == "interval"
            and p.get("name") == brush_name)
]

# Update (or remove) top-level params
if other_params:
    spec["params"] = other_params
else:
    spec.pop("params", None)

# Inject into the context (second) sub-view
if interval_params:
    ctx_view = spec["vconcat"][1]
    ctx_view["params"] = ctx_view.get("params", []) + interval_params

# ── Write self-contained HTML (uses same CDN versions as altair.to_html())
html = spec_to_html(
    spec,
    mode="vega-lite",
    vega_version="6",
    vegaembed_version="7",
    vegalite_version="6.4.1",
)

with open("chart.html", "w", encoding="utf-8") as f:
    f.write(html)

print("chart.html written successfully.")
