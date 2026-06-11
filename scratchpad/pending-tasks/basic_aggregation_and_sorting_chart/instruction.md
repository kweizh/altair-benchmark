Visualizing aggregate metrics and standardizing encodings is a fundamental first step in exploratory data analysis with Altair. Altair's shorthand syntax simplifies defining data types, but explicit sorting and tooltips require careful configuration.

You need to create a bar chart showing the average "Miles_per_Gallon" by "Origin" using the `cars` dataset from `vega_datasets` in a standard Python environment. 

**Constraints:**
- Must explicitly use Altair shorthand types (e.g., `:Q` for Quantitative, `:N` for Nominal).
- Bars MUST be sorted in descending order based on the average MPG.
- Tooltips must be added to display both the "Origin" and the computed average MPG.
- Save the resulting chart specification to a file named `bar_chart.json`.