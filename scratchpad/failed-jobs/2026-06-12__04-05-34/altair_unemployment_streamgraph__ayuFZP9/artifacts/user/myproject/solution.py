import os
import json
import altair as alt
from vega_datasets import data
from altair.utils.html import spec_to_html

# Disable max rows guard
alt.data_transformers.disable_max_rows()

# Dataset URL
source = data.unemployment_across_industries.url

# Hover selection
hover = alt.selection_point(
    name='hover',
    on='pointerover',
    nearest=True,
    encodings=['x'],
    empty=False
)

# 1. Base streamgraph layer
area = alt.Chart(source).mark_area(interpolate='monotone').encode(
    x=alt.X('date:T').timeUnit('yearmonth').title('Month'),
    y=alt.Y('count:Q').aggregate('sum').stack('center').axis(None),
    color=alt.Color('series:N').scale(scheme='category20b').title('Industry')
)

# 2. Hover ruler layer
rule = alt.Chart(source).mark_rule(color='gray', strokeWidth=1.5).encode(
    x=alt.X('date:T').timeUnit('yearmonth'),
    opacity=alt.condition(hover, alt.value(0.6), alt.value(0))
)

# 3. Top-series text annotation layer
text = alt.Chart(source).mark_text(
    align='left',
    dx=10,
    dy=10,
    fontSize=14,
    fontWeight='bold',
    color='black'
).encode(
    x=alt.X('date:T').timeUnit('yearmonth'),
    y=alt.value(20),  # Position near the top of the chart
    text=alt.Text('series:N'),
    opacity=alt.condition(hover, alt.value(1), alt.value(0))
).transform_window(
    rank='rank()',
    groupby=['date'],
    sort=[alt.SortField('count', order='descending')]
).transform_filter(
    alt.datum.rank == 1
)

# Combine layers and add selection parameter
chart = alt.layer(area, rule, text).add_params(hover).properties(
    width=800,
    height=400,
    title="US Unemployment Across Industries (Streamgraph with Hover Ruler and Top-Series Annotation)"
)

# Get the compiled spec dictionary
spec = chart.to_dict(context={"pre_transform": False})

# Post-process spec to ensure select.empty is false inside the point parameter
for param in spec.get('params', []):
    if 'select' in param and param['select'].get('type') == 'point':
        param['select']['empty'] = False

# Ensure output directory exists
os.makedirs('/home/user/myproject/out', exist_ok=True)

# Save to HTML file
html_content = spec_to_html(
    spec=spec,
    mode="vega-lite",
    vega_version=alt.VEGA_VERSION,
    vegaembed_version=alt.VEGAEMBED_VERSION,
    vegalite_version=alt.VEGALITE_VERSION
)

output_path = '/home/user/myproject/out/chart.html'
with open(output_path, 'w', encoding='utf-8') as f:
    f.write(html_content)

print(f"Successfully wrote chart HTML to {output_path}")
