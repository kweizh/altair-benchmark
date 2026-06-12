import pandas as pd
import altair as alt

# Construct wide-form data with exactly four columns and 12 rows
dates = pd.date_range(start="2025-01-01", periods=12, freq="MS")

df = pd.DataFrame({
    "Date": dates,
    "AAPL": [150.0, 152.5, 155.0, 153.0, 158.0, 160.0, 162.5, 161.0, 165.0, 168.0, 170.0, 172.5],
    "AMZN": [180.0, 182.0, 181.5, 185.0, 184.0, 188.0, 190.0, 189.5, 192.0, 195.0, 194.0, 198.0],
    "GOOG": [170.0, 171.5, 173.0, 172.5, 175.0, 177.0, 176.5, 179.0, 181.0, 180.5, 183.0, 185.0]
})

# Build the Vega-Altair chart using transform_fold
chart = alt.Chart(df).transform_fold(
    fold=["AAPL", "AMZN", "GOOG"],
    as_=["company", "price"]
).mark_line().encode(
    x=alt.X("Date", type="temporal"),
    y=alt.Y("price", type="quantitative"),
    color=alt.Color("company", type="nominal")
)

# Save the chart to /home/user/myproject/chart.html
chart.save("/home/user/myproject/chart.html")
print("Chart successfully built and saved to /home/user/myproject/chart.html")
