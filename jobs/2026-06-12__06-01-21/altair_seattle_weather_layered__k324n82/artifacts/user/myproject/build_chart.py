import altair as alt
from vega_datasets import data

# Shared base — URL-based source with explicit type shorthands
base = alt.Chart(data.seattle_weather.url).encode(
    alt.X("date:T", title="Date")
)

# ── Layer 1: Temperature range area (temp_min → temp_max) ──────────────
area = base.mark_area(opacity=0.3, color="orange").encode(
    alt.Y("temp_min:Q", title="Temperature (°C)"),
    alt.Y2("temp_max:Q"),
)

# ── Shared transform for mean temperature ──────────────────────────────
mean_base = base.transform_calculate(
    mean_temp="(datum.temp_min + datum.temp_max) / 2"
)

# ── Layer 2: Mean temperature line ─────────────────────────────────────
line = mean_base.mark_line(color="darkorange", strokeWidth=2).encode(
    alt.Y("mean_temp:Q")
)

# ── Layer 3: Precipitation bars on independent y scale ──────────────────
precip = base.mark_bar(opacity=0.5, color="steelblue").encode(
    alt.Y("precipitation:Q", title="Precipitation (mm)", axis=alt.Axis(titleColor="steelblue"))
)

# ── Layer 4: Dashed annotation rule at y = 0 °C ────────────────────────
rule_zero = base.mark_rule(color="gray", strokeDash=[4, 4]).encode(
    y=alt.datum(0)
)

# ── Layer 5: Hover interaction ─────────────────────────────────────────
# Selection: nearest-x point on pointerover
hover = alt.selection(
    type="point",
    on="pointerover",
    nearest=True,
    encodings=["x"],
    empty=False,
    name="hover",
)
# Force empty=False into the selection dict (Altair strips it as it's the default)
hover.select.empty = False

# Vertical rule that follows the hovered x position
hover_rule = mean_base.mark_rule(color="black", strokeWidth=1).encode(
    opacity=alt.when(hover).then(alt.value(1)).otherwise(alt.value(0))
).add_params(hover)

# Tooltip text for the hovered point
hover_text = mean_base.mark_text(
    align="left", dx=5, dy=-5, fontSize=11, fontWeight="bold"
).encode(
    text=alt.Text("label:N"),
    opacity=alt.when(hover).then(alt.value(1)).otherwise(alt.value(0)),
).transform_calculate(
    label="'Date: ' + format(datum.date, '%b %d, %Y') + '\\nMean Temp: ' + format(datum.mean_temp, '.1f') + '°C\\nPrecip: ' + format(datum.precipitation, '.1f') + ' mm'"
)

# ── Compose the layered chart ──────────────────────────────────────────
chart = alt.layer(
    area,
    line,
    precip,
    rule_zero,
    hover_rule,
    hover_text,
    data=data.seattle_weather.url,
).resolve_scale(
    y="independent"
).properties(
    title="Seattle Weather: Temperature & Precipitation",
    width=800,
    height=400,
)

# ── Save self-contained HTML ───────────────────────────────────────────
chart.save("/home/user/myproject/chart.html")

# ── Force empty=False into the selection spec in the HTML (Altair strips defaults) ──
import json, re
with open("/home/user/myproject/chart.html") as f:
    html = f.read()

match = re.search(r'var spec = ({.*?});', html, re.DOTALL)
spec = json.loads(match.group(1))

for param in spec.get("params", []):
    if param.get("name") == "hover" and "select" in param:
        param["select"]["empty"] = False

new_spec_json = json.dumps(spec)
html = html[:match.start(1)] + new_spec_json + html[match.end(1):]

with open("/home/user/myproject/chart.html", "w") as f:
    f.write(html)

print("✅ chart.html saved successfully")
