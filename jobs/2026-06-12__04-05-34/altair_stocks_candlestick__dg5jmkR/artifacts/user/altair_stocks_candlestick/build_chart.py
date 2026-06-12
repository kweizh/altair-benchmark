import os
import json
import pandas as pd
import altair as alt

def main():
    # 1. Read the OHLCV dataset from ohlcv.csv
    csv_path = 'ohlcv.csv'
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"Could not find {csv_path}")
    
    df = pd.read_csv(csv_path)
    
    # 2. Define the interval selection parameter constrained to the x (date) encoding
    brush = alt.selection_interval(
        name='brush',
        encodings=['x']
    )
    
    # 3. Upper view (candlestick)
    # Layered chart combining high-low wick and open-close body
    base = alt.Chart(df).encode(
        x=alt.X('date:T', scale=alt.Scale(domain=brush), title=None)
    )
    
    wick = base.mark_rule(color='black').encode(
        y=alt.Y('low:Q', scale=alt.Scale(zero=False), title='Price'),
        y2='high:Q'
    )
    
    body = base.mark_bar().encode(
        y='open:Q',
        y2='close:Q',
        color=alt.condition(
            'datum.open <= datum.close',
            alt.value('#069a2e'),  # green for up days
            alt.value('#e02130')   # red for down days
        )
    )
    
    upper_view = alt.layer(wick, body).properties(
        width=800,
        height=400,
        title='Stock Price (Candlestick Chart)'
    )
    
    # 4. Lower view (volume)
    lower_view = alt.Chart(df).mark_bar(color='steelblue').encode(
        x=alt.X('date:T', title='Date'),
        y=alt.Y('volume:Q', title='Volume')
    ).properties(
        width=800,
        height=100,
        title='Volume Overview'
    ).add_params(
        brush
    )
    
    # 5. Compose the two charts with vertical concatenation
    chart = alt.vconcat(upper_view, lower_view)
    
    # 6. Export to spec dict and modify to match strict acceptance criteria
    spec = chart.to_dict()
    
    # Locate the brush parameter from the top-level 'params'
    brush_param = None
    if 'params' in spec:
        for p in spec['params']:
            if p.get('name') == 'brush':
                brush_param = p
                break
    
    if brush_param:
        # Remove the top-level brush parameter
        spec['params'] = [p for p in spec['params'] if p.get('name') != 'brush']
        if not spec['params']:
            del spec['params']
        
        # Remove the 'views' field from the brush parameter as it is now local to the lower view
        if 'views' in brush_param:
            del brush_param['views']
            
        # Put the brush parameter in the lower view's params
        lower_view_spec = spec['vconcat'][1]
        if 'params' not in lower_view_spec:
            lower_view_spec['params'] = []
        lower_view_spec['params'].append(brush_param)
        
    # 7. Save chart.json
    with open('chart.json', 'w') as f:
        json.dump(spec, f, indent=2)
    print("Saved chart.json")
    
    # 8. Save chart.html with embedded spec
    html_template = """<!DOCTYPE html>
<html>
<head>
  <title>Interactive Candlestick + Volume Chart</title>
  <script src="https://cdn.jsdelivr.net/npm/vega@5"></script>
  <script src="https://cdn.jsdelivr.net/npm/vega-lite@5"></script>
  <script src="https://cdn.jsdelivr.net/npm/vega-embed@6"></script>
  <style>
    body {
      font-family: sans-serif;
      margin: 20px;
      background-color: #f9f9f9;
    }
    h1 {
      text-align: center;
      color: #333;
    }
    #vis {
      width: 100%;
      max-width: 900px;
      margin: 0 auto;
      background: white;
      padding: 20px;
      border-radius: 8px;
      box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
  </style>
</head>
<body>
  <h1>Interactive Candlestick & Volume Chart</h1>
  <div id="vis"></div>
  <script type="text/javascript">
    var spec = {SPEC_JSON};
    vegaEmbed('#vis', spec, {renderer: 'svg', actions: true})
      .then(function(result) {
        console.log("Chart successfully rendered!");
      })
      .catch(console.error);
  </script>
</body>
</html>
"""
    html_content = html_template.replace('{SPEC_JSON}', json.dumps(spec, indent=2))
    with open('chart.html', 'w') as f:
        f.write(html_content)
    print("Saved chart.html")

if __name__ == '__main__':
    main()
