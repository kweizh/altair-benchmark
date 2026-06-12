# Evaluation Dataset Research: Altair (Vega-Altair)

## 1. Library Overview
*   **Description**: Altair is a declarative statistical visualization library for Python, built on top of the [Vega-Lite](https://vega.github.io/vega-lite/) grammar. It allows users to describe visualizations in terms of data transformations and visual encodings rather than low-level imperative drawing commands.
*   **Ecosystem Role**: It is the standard declarative plotting library for the Python data science stack (Pandas, Polars, NumPy). It integrates deeply with Jupyter, VS Code, and Streamlit.
*   **Project Setup**:
    ```bash
    pip install altair vega_datasets
    # For large datasets (optional but recommended)
    pip install vegafusion[all]
    ```

## 2. Core Primitives & APIs

### Key Objects
*   **`alt.Chart(data)`**: The fundamental object. Data can be a Pandas DataFrame, Polars DataFrame, or a URL string pointing to a JSON/CSV file.
*   **`mark_*()`**: Defines the geometry (e.g., `mark_point()`, `mark_bar()`, `mark_line()`, `mark_area()`, `mark_rect()`, `mark_text()`).
*   **`encode()`**: Maps data columns to visual channels (e.g., `x`, `y`, `color`, `size`, `shape`, `tooltip`).
*   **`add_params()`**: (v5+) Replaces `add_selection`. Used to add interactive parameters like selections to a chart.

### Code Examples

#### Basic Chart with Shorthand Types
Altair uses a shorthand syntax for data types: `:Q` (Quantitative), `:N` (Nominal), `:O` (Ordinal), `:T` (Temporal), `:G` (GeoJSON). When the input is a pandas DataFrame, types are inferred; for URL or `alt.Data` inputs, types must be specified explicitly.
```python
import altair as alt
from altair.datasets import data

cars = data.cars()
chart = alt.Chart(cars).mark_point().encode(
    x='Horsepower:Q',
    y='Miles_per_Gallon:Q',
    color='Origin:N',
    tooltip=['Name', 'Origin']
).interactive() # Enables zoom/pan
```

#### Method-Based Syntax (Altair 5+)
The method-based syntax replaces verbose keyword arguments. Channel options like `axis`, `bin`, `scale`, and `title` are chainable methods on `alt.X` / `alt.Y` / `alt.Color`.
```python
alt.Chart(cars).mark_point().encode(
    alt.X('Horsepower')
        .axis(ticks=False)
        .bin(maxbins=10)
        .scale(domain=(30, 300), reverse=True),
    alt.Y('Miles_per_Gallon').title('Miles per Gallon'),
    color='Origin:N',
    shape='Origin:N',
)
```

#### Specifying Data: DataFrame, URL, Inline, GeoJSON
```python
import pandas as pd

# 1. pandas DataFrame (types auto-inferred)
df_chart = alt.Chart(pd.DataFrame({'x': ['A', 'B'], 'y': [5, 3]})).mark_bar().encode(x='x', y='y')

# 2. URL source (types MUST be declared)
url_chart = alt.Chart(data.cars.url).mark_point().encode(x='Horsepower:Q', y='Miles_per_Gallon:Q')

# 3. Inline JSON via alt.Data
inline_chart = alt.Chart(alt.Data(values=[{'x': 'A', 'y': 5}, {'x': 'B', 'y': 3}])
                         ).mark_bar().encode(x='x:N', y='y:Q')

# 4. GeoJSON via property selector
url_geojson = "https://d2ad6b4ur7yvpq.cloudfront.net/naturalearth-3.3.0/ne_110m_admin_0_countries.geojson"
geo_data = alt.Data(url=url_geojson, format=alt.DataFormat(property="features"))
geo_chart = alt.Chart(geo_data).mark_geoshape().encode(color='properties.continent:N')
```

#### Wide-to-Long Reshaping with Fold Transform
Altair works best with long-form data. The `transform_fold` reshapes wide data inside the spec without pre-processing in pandas.
```python
wide_form = pd.DataFrame({
    'Date': ['2007-10-01', '2007-11-01', '2007-12-01'],
    'AAPL': [189.95, 182.22, 198.08],
    'AMZN': [89.15, 90.56, 92.64],
    'GOOG': [707.00, 693.00, 691.48],
})

alt.Chart(wide_form).transform_fold(
    ['AAPL', 'AMZN', 'GOOG'],
    as_=['company', 'price']
).mark_line().encode(
    x='Date:T',
    y='price:Q',
    color='company:N',
)
```

#### Composition (Layering & Concatenation)
*   **Layering (`+` / `alt.layer`)**: Overlays charts; layer order determines z-order (later = on top).
*   **Horizontal Concatenation (`|` / `alt.hconcat`)**: Side-by-side.
*   **Vertical Concatenation (`&` / `alt.vconcat`)**: Top-to-bottom.
```python
stocks = data.stocks.url
base = alt.Chart(stocks).encode(
    x='date:T', y='price:Q', color='symbol:N'
).transform_filter(alt.datum.symbol == 'GOOG')

# Layer line + point + rule
layered = alt.layer(base.mark_line(), base.mark_point(), base.mark_rule()).interactive()

# Side-by-side scatter and histogram of the same column
scatter = alt.Chart(cars).mark_point().encode(x='Horsepower:Q', y='Miles_per_Gallon:Q')
hist = alt.Chart(cars).mark_bar().encode(alt.Y('Miles_per_Gallon:Q').bin(), x='count()')
dashboard = (scatter | hist).properties(title="Side by Side")
```

#### Binning & Aggregation (Histograms, 2D Bubble)
```python
# 1D histogram
alt.Chart(cars).mark_bar().encode(alt.X('Horsepower').bin(), y='count()')

# 2D bubble plot binned on both axes with mean color overlay
alt.Chart(cars).mark_circle().encode(
    alt.X('Horsepower').bin(),
    alt.Y('Miles_per_Gallon').bin(),
    size='count()',
    color='mean(Acceleration):Q',
)
```

#### Sort Options
The `sort` parameter accepts `'ascending'`, `'descending'`, an explicit list, an encoding name (e.g. `'-y'`), or `field`/`op` for aggregation-based sorting.
```python
barley = data.barley()

# Sort x-axis by mean yield aggregated from the data
alt.Chart(barley).mark_bar().encode(
    alt.X('site:N').sort(field='yield', op='mean'),
    y='mean(yield):Q',
)

# Sort with an explicit category order
alt.Chart(barley).mark_bar().encode(
    alt.X('site:N').sort(['Duluth', 'Grand Rapids', 'Morris',
                          'University Farm', 'Waseca', 'Crookston']),
    y='mean(yield):Q',
)
```

#### Datum vs. Value (Annotations & Reference Lines)
`alt.datum` operates in data units (via the scale); `alt.value` operates in raw visual units (pixels, CSS colors).
```python
source = data.stocks()
base = alt.Chart(source)
lines = base.mark_line().encode(x='date:T', y='price:Q', color='symbol:N')

# Horizontal rule at price=300 (data unit) and a vertical reference at year 2006
y_rule = base.mark_rule(strokeDash=[2, 2]).encode(y=alt.datum(300))
x_rule = base.mark_rule(strokeDash=[2, 2]).encode(
    x=alt.datum(alt.DateTime(year=2006)),
    color=alt.value("red"),  # explicit pixel-space color, ignores scale
)
lines + y_rule + x_rule
```

#### Advanced Interaction (v5+ Syntax)
Using `selection_interval` for cross-filtering, and `alt.when` for conditional encodings.
```python
brush = alt.selection_interval()

points = alt.Chart(cars).mark_point().encode(
    x='Horsepower:Q',
    y='Miles_per_Gallon:Q',
    color=alt.when(brush).then('Origin:N').otherwise(alt.value('lightgray'))
).add_params(brush)

bars = alt.Chart(cars).mark_bar().encode(
    y='Origin:N',
    x='count()',
    color='Origin:N'
).transform_filter(brush)

dashboard = points & bars
```

#### Hover-Driven Highlighting with `selection_point`
```python
hover = alt.selection_point(on='pointerover', nearest=True, empty=False)

base = alt.Chart(cars).encode(
    x=alt.X('Flipper_Length_mm:Q').scale(zero=False),
    y=alt.Y('Body_Mass_g:Q').scale(zero=False),
    color=alt.condition(hover, 'Origin:N', alt.value('lightgray')),
)
points = base.mark_point().add_params(hover)
text = base.mark_text(dy=-5).encode(
    text='Origin:N',
    opacity=alt.condition(hover, alt.value(1), alt.value(0)),
)
(points + text)
```

#### Linked Brushing with Focus + Context (Range Selection)
A classic overview-plus-detail pattern: a small overview chart hosts the brush, and the larger detail chart binds its x-domain to the brush.
```python
sp500 = data.sp500.url
brush = alt.selection_interval(encodings=['x'])

base = alt.Chart(sp500).mark_area().encode(
    x='date:T', y='price:Q'
).properties(width=600, height=200)

upper = base.encode(alt.X('date:T').scale(domain=brush))
lower = base.properties(height=60).add_params(brush)
focus_context = upper & lower
```

#### Repeat & Facet (Small Multiples)
```python
penguins = data.penguins.url

# Repeat: vary the encoding across panels
alt.Chart(penguins).mark_point().encode(
    alt.X(alt.repeat("column"), type='quantitative').scale(zero=False),
    alt.Y(alt.repeat("row"), type='quantitative').scale(zero=False),
    color='Species:N',
).properties(width=200, height=200).repeat(
    row=['Flipper Length (mm)', 'Body Mass (g)'],
    column=['Beak Length (mm)', 'Beak Depth (mm)'],
).interactive()

# Facet: vary the data subset across panels (one panel per species)
alt.Chart(penguins).mark_point().encode(
    x=alt.X('Flipper Length (mm):Q').scale(zero=False),
    y=alt.Y('Body Mass (g):Q').scale(zero=False),
    color='Species:N',
).properties(width=180, height=180).facet(column='Species:N')
```

#### Calculate, Filter & Window Transforms
```python
# transform_calculate + transform_filter
chart.transform_calculate(
    Efficiency='datum.Miles_per_Gallon / datum.Weight'
).transform_filter(
    alt.datum.Efficiency > 0.01
)

# transform_window: rolling 7-day average per company
alt.Chart(stocks).transform_window(
    rolling_mean='mean(price)',
    frame=[-3, 3],
    groupby=['symbol'],
).mark_line().encode(
    x='date:T',
    y='rolling_mean:Q',
    color='symbol:N',
)
```

#### Regression & LOESS Smoothing
```python
scatter = alt.Chart(cars).mark_point().encode(
    x='Horsepower:Q', y='Miles_per_Gallon:Q', color='Origin:N'
)
trend = alt.Chart(cars).transform_regression(
    'Horsepower', 'Miles_per_Gallon', groupby=['Origin']
).mark_line().encode(x='Horsepower:Q', y='Miles_per_Gallon:Q', color='Origin:N')

scatter + trend
```

#### Geographic Mapping with TopoJSON & Lookup
```python
from altair.datasets import data
counties = alt.topo_feature(data.us_10m.url, 'counties')
unemp = data.unemployment.url

alt.Chart(counties).mark_geoshape().transform_lookup(
    lookup='id',
    from_=alt.LookupData(unemp, key='id', fields=['rate']),
).encode(
    color=alt.Color('rate:Q').scale(scheme='blues'),
).project(type='albersUsa').properties(width=600, height=400)
```

#### Generated Data: Sequence + Calculate (a sine curve, no input data)
```python
alt.Chart(alt.sequence(0, 10, 0.1, as_='x')).transform_calculate(
    y='sin(datum.x)'
).mark_line().encode(x='x:Q', y='y:Q')
```

#### Widget Binding (Drop-down / Slider Controls)
```python
input_dropdown = alt.binding_select(options=['USA', 'Europe', 'Japan'], name='Origin: ')
origin_param = alt.param(value='USA', bind=input_dropdown)

alt.Chart(cars).mark_point().encode(
    x='Horsepower:Q',
    y='Miles_per_Gallon:Q',
    color=alt.when(alt.datum.Origin == origin_param)
            .then('Origin:N')
            .otherwise(alt.value('lightgray')),
).add_params(origin_param)
```

#### Scaling Large Data with VegaFusion + Inspecting Transformed Data
```python
import altair as alt
alt.data_transformers.enable('vegafusion')  # offload transforms to Python/Rust

# Inspect intermediate transformed data as a pandas DataFrame
chart = alt.Chart(data.cars.url).mark_bar().encode(
    y='Cylinders:O', x='mean_acc:Q'
).transform_aggregate(mean_acc='mean(Acceleration)', groupby=['Cylinders'])

chart.transformed_data()  # -> pandas DataFrame of post-transform rows
```

#### Save as html and verify in browser

```python
import altair as alt
from altair.datasets import data

chart = alt.Chart(data.cars.url).mark_point().encode(
    x='Horsepower:Q',
    y='Miles_per_Gallon:Q',
    color='Origin:N'
)

chart.save('chart.html')
```

By default, canvas is used for rendering the visualization in vegaEmbed. To change to svg rendering, use the embed_options as such:

```python
chart.save('chart.html', embed_options={'renderer':'svg'})
```

If an HTML string object is needed for further processing in custom HTML reports, you can use the Chart.to_html() method:

```python
html_string = chart.to_html()
# Use html_string in your custom HTML generation
```

And then, the html could be used in browser env.

## 3. Real-World Use Cases & Templates
*   **Interactive Dashboards**: Linked views where selecting data in one plot (e.g., a map or timeline) filters the others.
*   **Statistical Exploration**: Visualizing distributions with binned histograms and box plots.
*   **Geographic Mapping**: Using `mark_geoshape` with TopoJSON data.
*   **Integration with Streamlit**: Using `st.altair_chart` to build data apps with bidirectional communication (selections in Altair updating Streamlit state).

## 4. Developer Friction Points
1.  **MaxRowsError**: By default, Altair limits datasets to 5,000 rows to prevent browser crashes.
    *   *Solution*: Use `alt.data_transformers.disable_max_rows()` or `alt.data_transformers.enable('vegafusion')`.
2.  **Date Handling**: Passing Python `datetime` objects in selections or filters can sometimes fail if not converted correctly by the underlying Vega-Lite engine.
3.  **Complex Faceting**: Faceted charts with `resolve_scale(y='independent')` can be tricky when combined with shared selections across facets.
4.  **Encoding Conflicts**: Forgetting to specify data types (e.g., `:O` vs `:N`) can lead to unexpected axis sorting or color scales.
5.  **Browser Verification**: For generated HTML, you need to verify the output in a browser environment, make sure use `pochi-verifier` to do the verification.

## 5. Evaluation Ideas
*   **Simple**: Create a bar chart of average MPG by Origin with sorted bars and custom tooltips.
*   **Intermediate**: Build a layered plot showing a scatter plot of data points with a regression line (using `transform_regression`).
*   **Intermediate**: Implement an interactive "Focus + Context" chart (a small overview chart with a brush that controls the X-axis of a larger detail chart).
*   **Complex**: Create a cross-filtering dashboard with three linked views (Scatter, Histogram, and Heatmap) using `selection_point` and `selection_interval`.
*   **Complex**: Design a geographic map of US airports where clicking an airport highlights its connections on the same map (using `transform_lookup`).
*   **Edge Case**: Handle a 50,000-row dataset by configuring `VegaFusion` and implementing an aggregated heatmap to avoid browser lag.

## 6. Sources
1.  [Official Vega-Altair Documentation](https://altair-viz.github.io/): Main reference for API and User Guide.
2.  [Altair GitHub Repository](https://github.com/vega/altair): Source for issues and release notes.
3.  [Vega-Lite Documentation](https://vega.github.io/vega-lite/): Documentation for the underlying grammar.
4.  [VegaFusion Documentation](https://vegafusion.io/): Solutions for large dataset scaling.
5.  [Streamlit Altair Integration](https://docs.streamlit.io/develop/api-reference/charts/st.altair_chart): Guide for interactive web apps.