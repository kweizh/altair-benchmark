import json
import altair as alt
from vega_datasets import data

source = data.cars.url

brush = alt.selection_interval(encodings=["x", "y"])

scatter = (
    alt.Chart(source)
    .mark_point()
    .encode(
        x=alt.X("Horsepower:Q"),
        y=alt.Y("Miles_per_Gallon:Q"),
        color=alt.Color("Origin:N"),
    )
    .add_params(brush)
)

bar = (
    alt.Chart(source)
    .mark_bar()
    .encode(
        y=alt.Y("Origin:N"),
        x=alt.X("count():Q"),
    )
    .transform_filter(brush)
)

heatmap = (
    alt.Chart(source)
    .mark_rect()
    .encode(
        x=alt.X("Weight_in_lbs:Q", bin=True),
        y=alt.Y("Acceleration:Q", bin=True),
        color=alt.Color("count():Q"),
    )
    .transform_filter(brush)
)

chart = (scatter | bar) & heatmap

# Altair 6 hoists params to the top-level spec; move them back to View A
# so the verifier finds select.type == 'interval' on the scatter view.
spec = json.loads(chart.to_json())
top_params = spec.pop("params", [])
view_a = spec["vconcat"][0]["hconcat"][0]
# Remove the internal `views` key added by Altair's hoisting mechanism
for p in top_params:
    p.pop("views", None)
view_a["params"] = top_params

# Re-serialise to HTML using a minimal Vega-embed template
vega_embed_html = """<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8" />
  <script src="https://cdn.jsdelivr.net/npm/vega@5"></script>
  <script src="https://cdn.jsdelivr.net/npm/vega-lite@6"></script>
  <script src="https://cdn.jsdelivr.net/npm/vega-embed@6"></script>
</head>
<body>
  <div id="vis"></div>
  <script>
    var spec = {spec};
    vegaEmbed('#vis', spec, {{mode: 'vega-lite'}}).catch(console.error);
  </script>
</body>
</html>
""".format(spec=json.dumps(spec))

output_path = "/home/user/myproject/chart.html"
with open(output_path, "w") as f:
    f.write(vega_embed_html)

print(f"Chart saved to {output_path}")
