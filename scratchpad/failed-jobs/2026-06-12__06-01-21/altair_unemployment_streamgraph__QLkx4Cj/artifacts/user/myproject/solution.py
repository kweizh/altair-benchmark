import altair as alt

# Disable the default 5000-row limit so the full remote dataset is used.
alt.data_transformers.disable_max_rows()

# Remote dataset URL for unemployment across industries (long-form).
DATA_URL = "https://vega.github.io/vega-datasets/data/unemployment-across-industries.json"

# ---------------------------------------------------------------------------
# Base streamgraph layer
# ---------------------------------------------------------------------------
base = (
    alt.Chart(DATA_URL)
    .mark_area(interpolate="monotone")
    .encode(
        x=alt.X("yearmonth(date):T", axis=alt.Axis(title=None, format="%Y")),
        y=alt.Y("sum(count):Q", stack="center", axis=None),
        color=alt.Color("series:N", scale=alt.Scale(scheme="category20b"), legend=None),
    )
)

# ---------------------------------------------------------------------------
# Hover selection – nearest point on the X encoding, pointer-driven
# ---------------------------------------------------------------------------
hover = alt.selection_point(
    name="hover",
    on="pointerover",
    nearest=True,
    encodings=["x"],
    empty=False,
)

# ---------------------------------------------------------------------------
# Vertical rule layer – appears only when the hover selection has a value
# ---------------------------------------------------------------------------
rule = (
    alt.Chart(DATA_URL)
    .mark_rule(color="#888", strokeWidth=1)
    .encode(
        x="yearmonth(date):T",
        opacity=alt.condition(hover, alt.value(1), alt.value(0)),
    )
    .add_params(hover)
)

# ---------------------------------------------------------------------------
# Top-series annotation layer
#  1. Compute per-date rank of count descending via a window transform.
#  2. Filter to rank == 1 (the top series for each month).
#  3. Draw a text mark showing the series name and count.
# ---------------------------------------------------------------------------
annotation = (
    alt.Chart(DATA_URL)
    .mark_text(
        align="center",
        baseline="bottom",
        dy=-5,
        fontSize=11,
        fontWeight="bold",
    )
    .encode(
        x="yearmonth(date):T",
        y=alt.Y("sum(count):Q", stack="center"),
        text="label:N",
        opacity=alt.condition(hover, alt.value(1), alt.value(0)),
    )
    .transform_window(
        rank="rank()",
        groupby=["date"],
        sort=[alt.SortField("count", order="descending")],
    )
    .transform_filter(alt.datum.rank == 1)
    .transform_calculate(label="datum.series + ' (' + datum.count + ')'")
)

# ---------------------------------------------------------------------------
# Compose the final chart
# ---------------------------------------------------------------------------
chart = alt.layer(base, rule, annotation).properties(
    width=800,
    height=400,
    title="US Unemployment by Industry (Streamgraph)",
).configure_view(
    stroke=None,
)

# ---------------------------------------------------------------------------
# Save as a self-contained HTML file
# ---------------------------------------------------------------------------
import os, json

# Altair 5.5 does not serialize empty=False for point selections even though
# the parameter is accepted.  We patch the spec dict to include it explicitly.
spec = chart.to_dict()
for param in spec.get("params", []):
    sel = param.get("select")
    if sel is not None and sel.get("type") == "point":
        sel["empty"] = False

out_dir = "/home/user/myproject/out"
os.makedirs(out_dir, exist_ok=True)

# Write the HTML manually so we can inject the patched spec
html_template = """<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <script src="https://cdn.jsdelivr.net/npm/vega@5"></script>
  <script src="https://cdn.jsdelivr.net/npm/vega-lite@5"></script>
  <script src="https://cdn.jsdelivr.net/npm/vega-embed@6"></script>
</head>
<body>
  <div id="vis"></div>
  <script>
    vegaEmbed("#vis", {spec}, {{mode: "vega-lite"}})
      .catch(err => console.error(err));
  </script>
</body>
</html>"""

html = html_template.replace("{spec}", json.dumps(spec, indent=2))
with open(os.path.join(out_dir, "chart.html"), "w") as f:
    f.write(html)
print("Chart saved to /home/user/myproject/out/chart.html")
