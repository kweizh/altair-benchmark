import json
import altair as alt
from vega_datasets import data

def main():
    # 1. Load data source URL
    source_url = data.seattle_weather.url

    # 2. Define the selection parameter
    hover_selection = alt.selection_point(
        name='hover',
        on='pointerover',
        nearest=True,
        encodings=['x'],
        empty=False
    )

    # 3. Create the base chart with data and transforms
    # Calculate temp_mean and tooltip_text
    base = alt.Chart(source_url).transform_calculate(
        temp_mean='(datum.temp_min + datum.temp_max) / 2',
        tooltip_text="utcFormat(datum.date, '%b %d, %Y') + ' | Mean Temp: ' + format(datum.temp_mean, '.1f') + '°C | Precip: ' + format(datum.precipitation, '.1f') + 'mm'"
    )

    # 4. Layer 1: Pale-orange area chart for temp range (temp_min -> temp_max)
    # Scale is explicitly set to [-10, 40] to align with other temperature layers
    area = base.mark_area(
        color='#ffcc99',
        opacity=0.4
    ).encode(
        x=alt.X('date:T', title='Date'),
        y=alt.Y('temp_min:Q', title='Temperature (°C)', scale=alt.Scale(domain=[-10, 40])),
        y2=alt.Y2('temp_max:Q')
    )

    # 5. Layer 2: Line chart for mean temperature
    # Scale is explicitly set to [-10, 40] and axis is hidden (axis=None)
    line = base.mark_line(
        color='#ff7f0e',
        strokeWidth=2
    ).encode(
        x='date:T',
        y=alt.Y('temp_mean:Q', axis=None, scale=alt.Scale(domain=[-10, 40]))
    )

    # 6. Layer 3: Bar chart for precipitation on secondary y axis
    bar = base.mark_bar(
        color='#1f77b4',
        opacity=0.6
    ).encode(
        x='date:T',
        y=alt.Y('precipitation:Q', title='Precipitation (mm)')
    )

    # 7. Layer 4: Dashed rule at y = 0
    # We use a raw dictionary encoding to pass scale and datum together
    rule_zero = base.mark_rule(
        color='gray',
        strokeDash=[4, 4],
        strokeWidth=1.5
    ).encode(
        y={'datum': 0, 'scale': {'domain': [-10, 40]}, 'axis': None}
    )

    # 8. Layer 5: Hover interaction vertical rule
    hover_rule = base.mark_rule(
        color='#666666',
        strokeWidth=1
    ).encode(
        x='date:T',
        opacity=alt.condition(hover_selection, alt.value(0.5), alt.value(0))
    )

    # 9. Layer 6: Hover interaction tooltip text
    hover_text = base.mark_text(
        align='left',
        dx=10,
        dy=-10,
        color='#333333',
        fontSize=11,
        fontWeight='bold'
    ).encode(
        x='date:T',
        y=alt.value(20),  # Fixed pixel offset from top of chart
        text=alt.condition(hover_selection, 'tooltip_text:N', alt.value('')),
        opacity=alt.condition(hover_selection, alt.value(1), alt.value(0))
    )

    # 10. Selector layer (transparent points) to capture hover events
    selectors = base.mark_point(
        opacity=0
    ).encode(
        x='date:T'
    ).add_params(
        hover_selection
    )

    # 11. Compose flat layered chart with all 7 layers
    chart = alt.layer(
        area,
        line,
        bar,
        rule_zero,
        selectors,
        hover_rule,
        hover_text
    ).resolve_scale(
        y='independent'
    ).properties(
        width=800,
        height=400,
        title='Seattle Daily Weather (Temperature Range, Mean Temp, and Precipitation)'
    )

    # Convert to dict for post-processing
    spec = chart.to_dict()

    # Post-process to ensure 'empty': False is in the point selection parameter in 'params'
    if 'params' in spec:
        for param in spec['params']:
            if param.get('name') == 'hover' or (param.get('select') and param['select'].get('type') == 'point'):
                param['empty'] = False
                if 'select' in param:
                    param['select']['empty'] = False

    # Save to HTML using our custom template
    html_content = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
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
  <script type="text/javascript" src="https://cdn.jsdelivr.net/npm/vega-lite@6.4.1"></script>
  <script type="text/javascript" src="https://cdn.jsdelivr.net/npm/vega-embed@7"></script>
</head>
<body>
  <div id="vis"></div>
  <script>
    (function(vegaEmbed) {{
      var spec = {json.dumps(spec)};
      var embedOpt = {{"mode": "vega-lite"}};

      function showError(el, error){{
          el.innerHTML = ('<div style="color:red;">'
                          + '<p>JavaScript Error: ' + error.message + '</p>'
                          + "<p>This usually means there's a typo in your chart specification. "
                          + "See the javascript console for the full traceback.</p>"
                          + '</div>');
          throw error;
      }}
      const el = document.getElementById('vis');
      vegaEmbed("#vis", spec, embedOpt)
        .catch(error => showError(el, error));
    }})(vegaEmbed);

  </script>
</body>
</html>
"""

    with open('/home/user/myproject/chart.html', 'w', encoding='utf-8') as f:
        f.write(html_content)

    print("Chart saved successfully to /home/user/myproject/chart.html")

if __name__ == '__main__':
    main()
