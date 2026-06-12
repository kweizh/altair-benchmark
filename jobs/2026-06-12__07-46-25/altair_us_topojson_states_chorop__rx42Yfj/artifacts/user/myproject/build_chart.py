import json
import altair as alt
from vega_datasets import data

# Load state boundaries from TopoJSON
states = alt.topo_feature(data.us_10m.url, 'states')

# Get the lookup data source URL
source_url = data.population_engineers_hurricanes.url

# Create the choropleth map
chart = alt.Chart(states).mark_geoshape().transform_lookup(
    lookup='id',
    from_=alt.LookupData(source_url, key='id', fields=['state', 'engineers'])
).encode(
    color=alt.Color('engineers:Q', scale=alt.Scale(scheme='blues')),
    tooltip=['state:N', 'engineers:Q']
).project(
    type='albersUsa'
).properties(
    width=700,
    height=400
)

# Get the spec as a dictionary
spec_dict = chart.to_dict()

# Create the HTML content with spec embedded in a <script type="application/json"> block
html_content = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <title>US State-Level Engineers Choropleth</title>
  <style>
    #vis.vega-embed {{
      width: 100%;
      display: flex;
    }}

    #vis.vega-embed details,
    #vis.vega-embed details summary {{
      position: relative;
    }}
  </style>
  <script type="text/javascript" src="https://cdn.jsdelivr.net/npm/vega@6"></script>
  <script type="text/javascript" src="https://cdn.jsdelivr.net/npm/vega-lite@6"></script>
  <script type="text/javascript" src="https://cdn.jsdelivr.net/npm/vega-embed@7"></script>
</head>
<body>
  <div id="vis"></div>
  <script type="application/json" id="vega-spec">
{json.dumps(spec_dict, indent=2)}
  </script>
  <script type="text/javascript">
    const spec = JSON.parse(document.getElementById('vega-spec').textContent);
    const embedOpt = {{"mode": "vega-lite"}};
    vegaEmbed("#vis", spec, embedOpt).catch(console.error);
  </script>
</body>
</html>
"""

# Save to chart.html
with open('/home/user/myproject/chart.html', 'w') as f:
    f.write(html_content)

print("Chart successfully built and saved to /home/user/myproject/chart.html")
