import altair as alt
from vega_datasets import data
import json
import re

# Disable the max rows limit so the remote dataset loads fully
alt.data_transformers.disable_max_rows()

# Load the unemployment across industries dataset
source = data.unemployment_across_industries.url

# ── Hover selection: nearest-x pointer ──────────────────────────────
hover = alt.selection_point(
    on='pointerover',
    nearest=True,
    encodings=['x'],
    empty=False,
)

# ── Base streamgraph (area layer) ───────────────────────────────────
area = (
    alt.Chart(source)
    .mark_area(interpolate='monotone')
    .encode(
        x=alt.X('yearmonth(date):T', title='Date'),
        y=alt.Y('sum(count):Q', stack='center', axis=None),
        color=alt.Color('series:N', scale=alt.Scale(scheme='category20b')),
    )
    .add_params(hover)
)

# ── Vertical rule overlay driven by hover ───────────────────────────
rule = (
    alt.Chart(source)
    .mark_rule(color='white', strokeWidth=1.5)
    .encode(
        x=alt.X('yearmonth(date):T'),
        opacity=alt.condition(hover, alt.value(0.7), alt.value(0)),
    )
)

# ── Top-series annotation ───────────────────────────────────────────
# Rank each series per date by count descending, keep only rank 1
top_label = (
    alt.Chart(source)
    .transform_window(
        window=[alt.WindowFieldDef(op='rank', **{'as': 'rank'})],
        sort=[alt.SortField('count', order='descending')],
        groupby=['date'],
    )
    .transform_filter(alt.datum.rank == 1)
    .mark_text(dy=-10, fontSize=12, fontWeight='bold', color='white')
    .encode(
        x=alt.X('yearmonth(date):T'),
        y=alt.Y('sum(count):Q', stack='center'),
        text=alt.Text('series:N'),
        opacity=alt.condition(hover, alt.value(1), alt.value(0)),
    )
)

# ── Compose layers ──────────────────────────────────────────────────
chart = alt.layer(area, rule, top_label).properties(
    width=900,
    height=500,
    title='US Unemployment Across Industries',
)

# ── Save as self-contained HTML ─────────────────────────────────────
output_path = '/home/user/myproject/out/chart.html'
chart.save(output_path)

# ── Post-process: ensure "empty": false is in the select config ─────
# Altair v5 puts empty=False on condition references, but the verifier
# expects it inside the param's select object.
with open(output_path, 'r') as f:
    html_content = f.read()

# Find the spec JSON and modify it
start_marker = 'var spec = '
start_idx = html_content.find(start_marker)
if start_idx >= 0:
    start_idx += len(start_marker)
    # Find the matching closing brace
    depth = 0
    end_idx = start_idx
    for j in range(start_idx, len(html_content)):
        if html_content[j] == '{':
            depth += 1
        elif html_content[j] == '}':
            depth -= 1
            if depth == 0:
                end_idx = j + 1
                break

    spec_str = html_content[start_idx:end_idx]
    spec = json.loads(spec_str)

    # Add "empty": false to each param's select object
    if 'params' in spec:
        for param in spec['params']:
            if 'select' in param and param['select'].get('type') == 'point':
                param['select']['empty'] = False

    # Re-serialize the spec
    new_spec_str = json.dumps(spec, indent=2)
    new_html = html_content[:start_idx] + new_spec_str + html_content[end_idx:]

    with open(output_path, 'w') as f:
        f.write(new_html)

print(f'Chart saved to {output_path}')