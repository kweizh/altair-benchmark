import random
import pandas as pd
import altair as alt

# Enable VegaFusion data transformer to handle large datasets without MaxRowsError
alt.data_transformers.enable('vegafusion')

# Generate deterministic synthetic dataset with 60,000 rows
random.seed(42)

n = 60000
x_vals = [random.randint(0, 99) for _ in range(n)]
y_vals = [random.randint(0, 49) for _ in range(n)]
z_vals = [random.random() for _ in range(n)]

df = pd.DataFrame({'x': x_vals, 'y': y_vals, 'z': z_vals})

# Build a 2D binned heatmap chart
chart = alt.Chart(df).mark_rect().encode(
    x=alt.X('x:Q', bin=alt.Bin(maxbins=20)),
    y=alt.Y('y:Q', bin=alt.Bin(maxbins=20)),
    color=alt.Color('z:Q', aggregate='mean', scale=alt.Scale(scheme='magma'))
)

# Save the chart as a self-contained HTML file
chart.save('/home/user/myproject/chart.html')

# Extract the post-transform aggregated data and save as CSV
transformed_df = chart.transformed_data()
transformed_df.to_csv('/home/user/myproject/transformed_data.csv', index=False)