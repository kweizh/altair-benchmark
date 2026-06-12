import os
import json
import altair as alt
from vega_datasets import data

def main():
    # Define the project directory and file paths
    project_dir = "/home/user/altair_project"
    os.makedirs(project_dir, exist_ok=True)
    chart_path = os.path.join(project_dir, "chart.html")

    # Define the brush selection for the lower (context) chart, restricted to the x-axis
    brush = alt.selection_interval(name="brush", encodings=['x'])

    # Lower context chart: small height area chart with the brush parameter
    context = alt.Chart(data.sp500.url).mark_area().encode(
        x='date:T',
        y='price:Q'
    ).properties(
        width=600,
        height=60
    ).add_params(
        brush
    )

    # Upper detail chart: area chart whose x-scale domain is bound to the brush
    detail_area = alt.Chart(data.sp500.url).mark_area().encode(
        x=alt.X('date:T').scale(domain=brush),
        y='price:Q'
    ).properties(
        width=600,
        height=300
    )

    # Rule annotation: horizontal line at the running max price within the brushed window
    rule_chart = alt.Chart(data.sp500.url).transform_filter(
        brush
    ).transform_aggregate(
        max_price='max(price)'
    ).mark_rule(
        color='red',
        strokeWidth=2
    ).encode(
        y='max_price:Q'
    )

    # Layer the rule annotation on top of the detail area chart
    upper_layer = alt.layer(detail_area, rule_chart)

    # Vertically concatenate the upper layered chart and the lower context chart
    chart = alt.vconcat(upper_layer, context)

    # Get the JSON spec dictionary from the Altair chart
    spec = chart.to_dict()

    # Move the 'brush' parameter from the top-level 'params' to the second vconcat entry.
    # This satisfies the structural property: "The lower (second) vconcat entry declares a
    # selection_interval parameter restricted to the x encoding".
    params = spec.pop('params', [])
    brush_param = None
    for p in params:
        if p.get('name') == 'brush':
            brush_param = p
            break

    if brush_param:
        # Remove top-level 'views' list from the parameter to clean up the spec
        brush_param.pop('views', None)
        # Add 'params' to the second vconcat entry if not present
        if 'params' not in spec['vconcat'][1]:
            spec['vconcat'][1]['params'] = []
        spec['vconcat'][1]['params'].append(brush_param)

    # Generate the self-contained HTML file
    html_str = alt.utils.html.spec_to_html(
        spec,
        mode='vega-lite',
        vega_version=alt.VEGA_VERSION,
        vegalite_version=alt.VEGALITE_VERSION,
        vegaembed_version=alt.VEGAEMBED_VERSION
    )

    with open(chart_path, 'w') as f:
        f.write(html_str)

    print(f"Successfully generated focus + context dashboard at: {chart_path}")

if __name__ == "__main__":
    main()
