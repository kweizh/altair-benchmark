import altair as alt
import pandas as pd
import numpy as np

# Create wide-form DataFrame
dates = pd.date_range('2023-01-01', periods=12, freq='MS')
np.random.seed(42)
df = pd.DataFrame({
    'Date': dates,
    'AAPL': np.random.uniform(100, 150, 12),
    'AMZN': np.random.uniform(90, 130, 12),
    'GOOG': np.random.uniform(80, 120, 12)
})

# Create the chart
chart = alt.Chart(df).transform_fold(
    ['AAPL', 'AMZN', 'GOOG'],
    as_=['company', 'price']
).mark_line().encode(
    x='Date:T',
    y='price:Q',
    color='company:N'
)

# Save the chart
chart.save('/home/user/myproject/chart.html')
