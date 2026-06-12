import random
import pandas as pd
import altair as alt

# Enable VegaFusion data transformer to handle large datasets
alt.data_transformers.enable('vegafusion')

# Seed for deterministic reproducibility
random.seed(42)

# Generate 60,000 rows of synthetic data
n = 60_000
data = pd.DataFrame({
    'x': [random.randint(0, 99) for _ in range(n)],
    'y': [random.randint(0, 49) for _ in range(n)],
    'z': [random.random() for _ in range(n)],
})

# Build the 2D binned heatmap chart
chart = alt.Chart(data).mark_rect().encode(
    alt.X('x:Q', bin=alt.Bin(maxbins=20)),
    alt.Y('y:Q', bin=alt.Bin(maxbins=20)),
    alt.Color('z:Q', aggregate='mean', scale=alt.Scale(scheme='magma')),
)

# Save as self-contained HTML
chart.save('/home/user/myproject/chart.html')

# Extract post-transform aggregated data and write to CSV
transformed = chart.transformed_data()
transformed.to_csv('/home/user/myproject/transformed_data.csv', index=False)

print(f"Chart saved to /home/user/myproject/chart.html")
print(f"Transformed data saved to /home/user/myproject/transformed_data.csv ({len(transformed)} rows)")
