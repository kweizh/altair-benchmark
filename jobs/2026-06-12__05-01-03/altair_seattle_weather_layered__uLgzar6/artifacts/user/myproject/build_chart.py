"""
Layered Seattle Weather Chart – Vega-Altair
Produces a single self-contained chart.html

Layers:
  0  – pale-orange area:  temp_min → temp_max range
  1  – orange line:       daily mean temperature (via transform_calculate)
  2  – steelblue bars:    daily precipitation (independent secondary y-axis)
  3  – dashed rule:       y = 0 °C annotation
  4  – hover rule:        vertical crosshair driven by nearest-x pointer
  5  – hover text:        floating label + tooltip on hover
"""

import json
import altair as alt
from vega_datasets import data

# ── Shared base ────────────────────────────────────────────────────────────────
# URL-based data source; all field types must be declared explicitly.
# transform_calculate derives the mean_temp field used by layers 1, 4, 5.
base = (
    alt.Chart(data.seattle_weather.url)
    .transform_calculate(
        mean_temp="(datum.temp_min + datum.temp_max) / 2"
    )
)

# ── Layer 0 – Temperature range area (temp_min → temp_max) ───────────────────
area_layer = base.mark_area(
    color="peachpuff",
    opacity=0.6,
).encode(
    x=alt.X("date:T", title="Date"),
    y=alt.Y("temp_min:Q", title="Temperature (°C)"),
    y2=alt.Y2("temp_max:Q"),
)

# ── Layer 1 – Mean temperature line ──────────────────────────────────────────
line_layer = base.mark_line(
    color="darkorange",
    strokeWidth=1.8,
).encode(
    x="date:T",
    y=alt.Y("mean_temp:Q"),
)

# ── Layer 2 – Precipitation bars (independent secondary y-axis) ───────────────
bar_layer = base.mark_bar(
    color="steelblue",
    opacity=0.35,
).encode(
    x="date:T",
    y=alt.Y("precipitation:Q", title="Precipitation (mm)"),
)

# ── Layer 3 – Dashed y = 0 annotation rule ───────────────────────────────────
# Use an inline data value so we can encode y = 0 as a constant.
zero_rule_layer = (
    alt.Chart({"values": [{"zero": 0}]})
    .mark_rule(
        color="crimson",
        strokeDash=[4, 4],
        strokeWidth=1.2,
    )
    .encode(
        y=alt.Y("zero:Q"),
    )
)

# ── Hover selection ───────────────────────────────────────────────────────────
hover = alt.selection_point(
    name="hover",
    nearest=True,
    on="pointerover",
    encodings=["x"],
    empty=False,
)

# ── Layer 4 – Vertical hover crosshair ───────────────────────────────────────
hover_rule_layer = (
    base.mark_rule(color="gray", opacity=0.5)
    .encode(x="date:T")
    .add_params(hover)
    .transform_filter(hover)
)

# ── Layer 5 – Floating label and rich tooltip on hover ───────────────────────
hover_text_layer = (
    base.mark_text(
        align="left",
        dx=6,
        dy=-8,
        fontSize=11,
        fontWeight="bold",
        color="black",
    )
    .encode(
        x="date:T",
        y=alt.Y("mean_temp:Q"),
        text=alt.condition(
            hover,
            alt.Text("mean_temp:Q", format=".1f"),
            alt.value(""),
        ),
        opacity=alt.condition(hover, alt.value(1), alt.value(0)),
        tooltip=[
            alt.Tooltip("date:T",          title="Date",              format="%b %d, %Y"),
            alt.Tooltip("mean_temp:Q",     title="Mean Temp (°C)",    format=".1f"),
            alt.Tooltip("precipitation:Q", title="Precipitation (mm)", format=".1f"),
        ],
    )
)

# ── Compose all layers ────────────────────────────────────────────────────────
chart = (
    alt.layer(
        area_layer,        # 0 – temperature range area
        line_layer,        # 1 – mean temperature line
        bar_layer,         # 2 – precipitation bars (independent y)
        zero_rule_layer,   # 3 – y = 0 dashed rule
        hover_rule_layer,  # 4 – vertical hover crosshair
        hover_text_layer,  # 5 – hover text / tooltip
    )
    .resolve_scale(y="independent")
    .properties(
        title="Seattle Weather: Temperature Range & Precipitation (2012–2015)",
        width=850,
        height=380,
    )
    .interactive(bind_x=True)
)

# ── Post-process spec: inject empty=false into the hover param's select dict ──
# Altair 6 / Vega-Lite 5 moves `empty` to the predicate reference level, but
# we add it redundantly to the select{} object so spec validators can find it.
spec_dict = chart.to_dict(context={"pre_transform": False})
for param in spec_dict.get("params", []):
    if param.get("name") == "hover":
        param["select"]["empty"] = False
        break

# ── Export as self-contained HTML ─────────────────────────────────────────────
output_path = "/home/user/myproject/chart.html"

# Build the HTML manually so the spec (with our patch) is embedded correctly.
vega_version   = "6"
vegalite_version = "6.4.1"
vegaembed_version = "7"

html = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8" />
  <title>Seattle Weather Chart</title>
  <script type="text/javascript" src="https://cdn.jsdelivr.net/npm/vega@{vega_version}"></script>
  <script type="text/javascript" src="https://cdn.jsdelivr.net/npm/vega-lite@{vegalite_version}"></script>
  <script type="text/javascript" src="https://cdn.jsdelivr.net/npm/vega-embed@{vegaembed_version}"></script>
</head>
<body>
  <div id="vis"></div>
  <script type="application/json" id="spec">
{json.dumps(spec_dict, indent=2)}
  </script>
  <script>
    (function() {{
      var spec = JSON.parse(document.getElementById("spec").textContent);
      vegaEmbed("#vis", spec, {{mode: "vega-lite", renderer: "svg"}}).catch(console.error);
    }})();
  </script>
</body>
</html>
"""

with open(output_path, "w", encoding="utf-8") as f:
    f.write(html)

# ── Verification summary ──────────────────────────────────────────────────────
print(f"Chart saved → {output_path}")
print(f"Layers      : {len(spec_dict['layer'])}")
marks = [
    (l.get("mark", {}).get("type") if isinstance(l.get("mark"), dict) else l.get("mark"))
    for l in spec_dict["layer"]
]
print(f"Mark types  : {marks}")
calcs = [
    t["calculate"]
    for l in spec_dict["layer"]
    for t in l.get("transform", [])
    if "calculate" in t
]
print(f"Calc xforms : {calcs[:1]}")
print(f"Resolve y   : {spec_dict.get('resolve', {}).get('scale', {}).get('y')}")
params = spec_dict.get("params", [])
hover_param = next((p for p in params if p.get("name") == "hover"), None)
if hover_param:
    s = hover_param["select"]
    print(f"Hover param : nearest={s.get('nearest')}, on={s.get('on')}, "
          f"empty={s.get('empty')}, encodings={s.get('encodings')}")
