"""
build_chart.py
==============
Builds an interactive candlestick + volume chart from ohlcv.csv using
Vega-Altair and saves the result as chart.html and chart.json.

Chart layout
------------
Upper view (candlestick)
  - mark_rule  : high–low wick  (y=low, y2=high)
  - mark_bar   : open–close body (y=open, y2=close, color by up/down day)

Lower view (volume overview)
  - mark_bar   : daily volume
  - hosts an interval brush restricted to the x (date) axis

Interaction
-----------
Brushing on the lower volume chart zooms / pans the upper candlestick view
by binding the upper chart's x-scale domain to the brush parameter.
"""

import json
import re

import altair as alt
import pandas as pd

# ---------------------------------------------------------------------------
# 1. Load data
# ---------------------------------------------------------------------------
df = pd.read_csv("ohlcv.csv", parse_dates=["date"])

# ---------------------------------------------------------------------------
# 2. Interval brush — will be attached to the lower view
# ---------------------------------------------------------------------------
BRUSH_NAME = "brush"
brush = alt.selection_interval(encodings=["x"], name=BRUSH_NAME)

# ---------------------------------------------------------------------------
# 3. Color encoding for candlestick bodies
#    Green (#26a69a) for up days (close >= open), red (#ef5350) for down days
# ---------------------------------------------------------------------------
body_color = alt.condition(
    "datum.open <= datum.close",
    alt.value("#26a69a"),  # bullish — teal/green
    alt.value("#ef5350"),  # bearish — red
)

# ---------------------------------------------------------------------------
# 4. Upper view — layered candlestick
#    The x scale domain is bound to the brush parameter by name.
# ---------------------------------------------------------------------------
x_upper = alt.X(
    "date:T",
    scale=alt.Scale(domain=brush),
    axis=alt.Axis(title=None, format="%b %d", labelAngle=-30),
)

# 4a. Wick layer: rule from low to high
wick = (
    alt.Chart(df)
    .mark_rule(strokeWidth=1)
    .encode(
        x=x_upper,
        y=alt.Y("low:Q", scale=alt.Scale(zero=False), title="Price (USD)"),
        y2=alt.Y2("high:Q"),
        color=body_color,
    )
)

# 4b. Body layer: bar from open to close
body = (
    alt.Chart(df)
    .mark_bar()
    .encode(
        x=x_upper,
        y=alt.Y("open:Q", scale=alt.Scale(zero=False), title="Price (USD)"),
        y2=alt.Y2("close:Q"),
        color=body_color,
        tooltip=[
            alt.Tooltip("date:T", title="Date", format="%Y-%m-%d"),
            alt.Tooltip("open:Q", title="Open", format="$.2f"),
            alt.Tooltip("high:Q", title="High", format="$.2f"),
            alt.Tooltip("low:Q", title="Low", format="$.2f"),
            alt.Tooltip("close:Q", title="Close", format="$.2f"),
        ],
    )
)

candlestick = (
    alt.layer(wick, body)
    .properties(
        width=900,
        height=400,
        title=alt.TitleParams(
            "Daily Candlestick Chart",
            subtitle="Brush the volume panel below to zoom / pan",
            fontSize=16,
            subtitleFontSize=12,
        ),
    )
)

# ---------------------------------------------------------------------------
# 5. Lower view — volume bars with the brush parameter
# ---------------------------------------------------------------------------
x_lower = alt.X(
    "date:T",
    axis=alt.Axis(title="Date", format="%b %Y", labelAngle=-30),
)

volume = (
    alt.Chart(df)
    .mark_bar(opacity=0.8)
    .encode(
        x=x_lower,
        y=alt.Y(
            "volume:Q",
            axis=alt.Axis(title="Volume", format="~s"),
        ),
        color=alt.condition(
            "datum.open <= datum.close",
            alt.value("#26a69a"),
            alt.value("#ef5350"),
        ),
        tooltip=[
            alt.Tooltip("date:T", title="Date", format="%Y-%m-%d"),
            alt.Tooltip("volume:Q", title="Volume", format=","),
        ],
    )
    .add_params(brush)
    .properties(width=900, height=120, title="")
)

# ---------------------------------------------------------------------------
# 6. Compose vertically
# ---------------------------------------------------------------------------
chart = alt.vconcat(candlestick, volume).configure_view(stroke=None)

# ---------------------------------------------------------------------------
# 7. Obtain the raw Vega-Lite spec dict
# ---------------------------------------------------------------------------
spec = chart.to_dict()

# ---------------------------------------------------------------------------
# 8. Post-process: Altair 6 hoists selection parameters to the top level and
#    adds a "views" array.  The acceptance criteria require the interval
#    selection to appear in the *lower view's* params list.
#    We therefore:
#      a) Find the top-level param entry for "brush".
#      b) Strip "views" from it (it's not needed once it lives inline).
#      c) Remove it from the top-level "params" list.
#      d) Insert it into the lower view's "params" list.
# ---------------------------------------------------------------------------
top_params = spec.get("params", [])
brush_param = None
remaining_top_params = []

for p in top_params:
    if p.get("name") == BRUSH_NAME:
        # Keep only the core selection definition; drop "views"
        brush_param = {k: v for k, v in p.items() if k != "views"}
    else:
        remaining_top_params.append(p)

if brush_param is None:
    raise RuntimeError(
        f"Could not locate the '{BRUSH_NAME}' parameter in the top-level spec. "
        "Altair may have changed how it serialises selection parameters."
    )

# Update top-level params (remove or drop the key entirely if empty)
if remaining_top_params:
    spec["params"] = remaining_top_params
else:
    spec.pop("params", None)

# Insert into the lower view (vconcat[1])
lower_view = spec["vconcat"][1]
lower_view.setdefault("params", [])
lower_view["params"].insert(0, brush_param)

# Also clean up any auto-generated "name" on the lower view chart
# (Altair adds it so it can populate "views"; it's harmless but tidy to remove)
lower_view.pop("name", None)

# ---------------------------------------------------------------------------
# 9. Persist artefacts
# ---------------------------------------------------------------------------
json_str = json.dumps(spec, indent=2)

with open("chart.json", "w") as f:
    f.write(json_str)
print("Saved chart.json")

# Build a self-contained HTML file with vega-embed
html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Candlestick + Volume Chart</title>
  <script src="https://cdn.jsdelivr.net/npm/vega@5"></script>
  <script src="https://cdn.jsdelivr.net/npm/vega-lite@5"></script>
  <script src="https://cdn.jsdelivr.net/npm/vega-embed@6"></script>
  <style>
    body {{
      font-family: sans-serif;
      display: flex;
      justify-content: center;
      padding: 2rem;
      background: #fafafa;
    }}
    #vis {{ width: 100%; }}
  </style>
</head>
<body>
  <div id="vis"></div>
  <script>
    const spec = {json_str};
    vegaEmbed('#vis', spec, {{renderer: 'svg', actions: true}});
  </script>
</body>
</html>
"""

with open("chart.html", "w") as f:
    f.write(html)
print("Saved chart.html")
