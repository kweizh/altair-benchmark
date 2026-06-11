Dashboards often require linked views where selecting or brushing data in one visual updates the subset of data displayed in the others, providing deep multi-dimensional exploration.

You need to create a cross-filtering dashboard comprising three linked views (a scatter plot, a bar chart, and a histogram) using the `cars` dataset. 

**Constraints:**
- Apply an interval selection brush (`alt.selection_interval()`) to the scatter plot.
- The bar chart and histogram MUST dynamically filter their displayed data based on the scatter plot's brush using `transform_filter`.
- Unselected points in the scatter plot should turn `lightgray` using an `alt.when().then().otherwise()` condition.
- Save the complete dashboard layout to `dashboard.html`.