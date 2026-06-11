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
Altair uses a shorthand syntax for data types: `:Q` (Quantitative), `:N` (Nominal), `:O` (Ordinal), `:T` (Temporal).
```python
import altair as alt
from vega_datasets import data

cars = data.cars()
chart = alt.Chart(cars).mark_point().encode(
    x='Horsepower:Q',
    y='Miles_per_Gallon:Q',
    color='Origin:N',
    tooltip=['Name', 'Origin']
).interactive() # Enables zoom/pan
```

#### Composition (Layering & Concatenation)
*   **Layering (`+`)**: Overlays charts.
*   **Horizontal Concatenation (`|`)**: Side-by-side.
*   **Vertical Concatenation (`&`)**: Top-to-bottom.
```python
base = alt.Chart(cars).encode(x='Horsepower:Q')
layers = base.mark_bar() + base.mark_rule(color='red').transform_aggregate(x='mean(Horsepower)')
concat = (chart1 | chart2).properties(title="Side by Side")
```

#### Advanced Interaction (v5+ Syntax)
Using `selection_interval` for cross-filtering.
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

#### Transformations
```python
chart.transform_calculate(
    Efficiency='datum.Miles_per_Gallon / datum.Weight'
).transform_filter(
    alt.datum.Efficiency > 0.01
)
```

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