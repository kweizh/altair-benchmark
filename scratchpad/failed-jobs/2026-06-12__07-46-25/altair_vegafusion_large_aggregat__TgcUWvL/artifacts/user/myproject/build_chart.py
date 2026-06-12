import random
import pandas as pd
import altair as alt

# 1. Generate a deterministic synthetic dataset using Python's random module
random.seed(42)
n_rows = 60000

x_data = []
y_data = []
z_data = []

for _ in range(n_rows):
    x_data.append(random.randint(0, 99))
    y_data.append(random.randint(0, 49))
    z_data.append(random.random())

df = pd.DataFrame({
    'x': x_data,
    'y': y_data,
    'z': z_data
})

# 2. Enable the VegaFusion data transformer globally
alt.data_transformers.enable('vegafusion')

# 3. Build the 2D binned heatmap chart using mark_rect()
chart = alt.Chart(df).mark_rect().encode(
    x=alt.X('x:Q', bin=alt.Bin(maxbins=20)),
    y=alt.Y('y:Q', bin=alt.Bin(maxbins=20)),
    color=alt.Color('z:Q', aggregate='mean', scale=alt.Scale(scheme='magma'))
)

# 4. Save the chart as a self-contained HTML file
chart.save('/home/user/myproject/chart.html')

# 5. Extract the post-transform aggregated DataFrame and save as CSV
transformed_df = chart.transformed_data()
transformed_df.to_csv('/home/user/myproject/transformed_data.csv', index=False)

print(f"Successfully generated chart.html and transformed_data.csv with {len(transformed_df)} rows.")
