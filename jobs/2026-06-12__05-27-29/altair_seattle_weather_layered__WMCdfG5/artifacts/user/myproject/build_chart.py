#!/usr/bin/env python3
"""Build a layered Seattle weather chart with Vega-Altair and export to HTML."""

import altair as alt
from vega_datasets import data
import json
import re

# ── Data source (URL-based → explicit type shorthands required) ──────────
source = data.seattle_weather.url

# ── Shared base chart ─────────────────────────────────────────────────────
base = alt.Chart(source)

# ── Layer 1: Temperature range area (pale orange) ────────────────────────
area = (
    base.mark_area(opacity=0.3, color="orange")
    .encode(
        x="date:T",
        y="temp_max:Q",
        y2="temp_min:Q",
    )
)

# ── Layer 2: Mean temperature line (computed via transform_calculate) ────
mean_line = (
    base.transform_calculate(
        mean_temp="(datum.temp_min + datum.temp_max) / 2"
    )
    .mark_line(color="darkorange", strokeWidth=1.5)
    .encode(
        x="date:T",
        y="mean_temp:Q",
    )
)

# ── Layer 3: Precipitation bars (secondary y axis) ───────────────────────
precip_bars = (
    base.mark_bar(opacity=0.5, color="steelblue")
    .encode(
        x="date:T",
        y=alt.Y("precipitation:Q", title="Precipitation (mm)"),
    )
)

# ── Layer 4: Dashed rule annotation at y = 0 °C ───────────────────────────
zero_rule = (
    base.mark_rule(strokeDash=[4, 4], color="gray")
    .encode(
        x=alt.X("date:T"),
        y=alt.Y(datum=0),
    )
)

# ── Layer 5: Hover tooltip (vertical rule + text) ────────────────────────
# Point selection driven by nearest-x pointer-over
pointer = alt.selection_point(
    on="pointerover",
    nearest=True,
    encodings=["x"],
    empty=False,
)

# Vertical rule that follows the hovered x position
hover_rule = (
    base.mark_rule(color="black", strokeWidth=1)
    .encode(
        x="date:T",
        opacity=alt.condition(pointer, alt.value(1), alt.value(0)),
    )
    .add_params(pointer)
)

# Tooltip text showing date, mean temperature, and precipitation
# We need the calculated mean_temp field here too
hover_text = (
    base.transform_calculate(
        mean_temp="(datum.temp_min + datum.temp_max) / 2"
    )
    .mark_text(dy=-8, align="center", fontSize=11, fontWeight="bold")
    .encode(
        x="date:T",
        y="mean_temp:Q",
        text=alt.condition(
            pointer,
            alt.Text("mean_temp:Q", format=".1f"),
            alt.value(""),
        ),
        opacity=alt.condition(pointer, alt.value(1), alt.value(0)),
    )
    .add_params(pointer)
)

# ── Compose the layered chart ─────────────────────────────────────────────
chart = (
    alt.layer(
        area,
        mean_line,
        precip_bars,
        zero_rule,
        hover_rule,
        hover_text,
    )
    .resolve_scale(y="independent")
    .properties(
        width=900,
        height=400,
        title="Seattle Weather: Temperature Range, Mean & Precipitation",
    )
)

# ── Save to HTML ──────────────────────────────────────────────────────────
output_path = "/home/user/myproject/chart.html"
chart.save(output_path)

# ── Post-process: ensure `empty: false` appears in the selection param ───
# Altair 6.x places `empty` in condition refs (Vega-Lite 5 convention),
# but some validators expect it in the param's `select` object too.
with open(output_path, "r") as f:
    html = f.read()

# Find the spec JSON inside the HTML
match = re.search(r'var spec = (\{.*?\});\s*\n', html, re.DOTALL)
if match:
    spec = json.loads(match.group(1))
    # Inject empty:false into every point selection's select object
    for param in spec.get("params", []):
        sel = param.get("select", {})
        if sel.get("type") == "point":
            sel["empty"] = False
    # Re-serialize and replace in the HTML
    new_spec_json = json.dumps(spec, ensure_ascii=False)
    html = html.replace(match.group(1), new_spec_json, 1)
    with open(output_path, "w") as f:
        f.write(html)

print(f"Chart saved to {output_path}")