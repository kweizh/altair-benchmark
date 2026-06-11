Altair excels at visual composition, allowing developers to overlay analytical transformations directly on top of raw data visualizations using the layering operator (`+`).

You need to build a layered chart containing a base scatter plot of "Horsepower" (X-axis) versus "Miles_per_Gallon" (Y-axis) from the `cars` dataset, and overlay a linear regression line in a Python script.

**Constraints:**
- The regression line MUST be calculated natively within Altair using `transform_regression`.
- The scatter plot points and the regression line must be distinct colors (e.g., blue for points, red for the line).
- Do NOT pre-calculate the regression line using Pandas or NumPy.
- Save the rendered chart to a file named `regression_chart.html`.