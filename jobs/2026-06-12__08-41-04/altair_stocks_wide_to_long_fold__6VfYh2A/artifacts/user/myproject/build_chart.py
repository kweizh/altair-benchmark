import pandas as pd
import altair as alt

# Build a wide-form DataFrame with monthly stock prices for 12 months
dates = pd.date_range("2023-01-01", periods=12, freq="MS")

data = pd.DataFrame({
    "Date": dates,
    "AAPL": [130, 150, 155, 165, 175, 190, 185, 178, 172, 180, 188, 195],
    "AMZN": [95,  105, 100, 110, 120, 128, 132, 125, 118, 122, 130, 138],
    "GOOG": [88,  95,  98,  105, 115, 120, 117, 112, 108, 113, 119, 125],
})

# Build the chart using transform_fold to reshape wide → long inside the spec
chart = (
    alt.Chart(data)
    .mark_line()
    .transform_fold(
        fold=["AAPL", "AMZN", "GOOG"],
        as_=["company", "price"],
    )
    .encode(
        x=alt.X("Date:T", title="Date"),
        y=alt.Y("price:Q", title="Price (USD)"),
        color=alt.Color("company:N", title="Company"),
    )
    .properties(
        title="Monthly Stock Prices (2023)",
        width=600,
        height=350,
    )
)

chart.save("/home/user/myproject/chart.html")
print("Saved chart to /home/user/myproject/chart.html")
