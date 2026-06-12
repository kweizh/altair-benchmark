import altair as alt
from vega_datasets import data
import json
import re

def build_chart():
    # Source URL for the Cars dataset
    source = data.cars.url

    # Selection parameter for hover interaction
    hover = alt.selection_point(
        name="hover",
        on="pointerover",
        nearest=True,
        empty=False
    )

    # Base chart with shared X and Y encodings
    base = alt.Chart(source).encode(
        x=alt.X('Horsepower:Q').scale(zero=False),
        y=alt.Y('Miles_per_Gallon:Q').scale(zero=False)
    )

    # Point layer
    points = base.mark_point().encode(
        color=alt.condition(hover, 'Origin:N', alt.value('lightgray'))
    ).add_params(
        hover
    )

    # Text layer
    text = base.mark_text(dy=-10).encode(
        text='Name:N',
        opacity=alt.condition(hover, alt.value(1), alt.value(0))
    )

    # Combined layered chart
    chart = alt.layer(points, text).properties(
        width=600,
        height=400
    )

    # Save to HTML
    html_path = '/home/user/myproject/chart.html'
    chart.save(html_path)

    # Post-process the HTML to ensure "empty": false is explicitly declared 
    # within the selection parameter definition under "params" in the Vega-Lite spec.
    with open(html_path, 'r') as f:
        content = f.read()

    # Find the JSON spec using a regular expression
    spec_match = re.search(r'var spec = (\{.*?\});', content)
    if spec_match:
        spec_json = spec_match.group(1)
        spec = json.loads(spec_json)
        
        # Modify the spec to ensure "empty": false is in the parameter definition
        if 'params' in spec:
            for param in spec['params']:
                if param.get('name') == 'hover':
                    # Add empty: False to both the param top-level and select block to be absolutely safe
                    param['empty'] = False
                    if 'select' in param:
                        if isinstance(param['select'], dict):
                            param['select']['empty'] = False
                        elif isinstance(param['select'], str):
                            param['select'] = {'type': param['select'], 'empty': False}
        
        # Serialize back to JSON and replace in content
        new_spec_json = json.dumps(spec)
        new_content = content.replace(spec_json, new_spec_json)
        
        with open(html_path, 'w') as f:
            f.write(new_content)
        print("Chart built and post-processed successfully!")
    else:
        print("Warning: Could not find spec in HTML to post-process.")

if __name__ == '__main__':
    build_chart()
