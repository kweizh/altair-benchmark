import pandas as pd
import altair as alt

# Construct wide-form DataFrame with monthly stock prices
dates = pd.date_range(start="2024-01-01", periods=12, freq="MS")

data = pd.DataFrame({
    "Date": dates,
    "AAPL": [185.0, 188.5, 192.3, 189.7, 194.1, 198.6, 201.2, 205.8, 210.3, 215.0, 218.4, 222.1],
    "AMZN": [155.0, 158.2, 162.5, 160.1, 165.8, 170.3, 174.9, 179.6, 183.2, 188.0, 192.5, 196.8],
    "GOOG": [140.0, 142.5, 145.8, 143.2, 148.1, 152.6, 155.3, 159.7, 163.4, 167.8, 171.2, 175.0],
})

# Build chart using transform_fold to reshape wide form to long form
chart = (
    alt.Chart(data)
    .transform_fold(["AAPL", "AMZN", "GOOG"], as_=["company", "price"])
    .mark_line()
    .encode(
        x=alt.X("Date:T", title="Date"),
        y=alt.Y("price:Q", title="Price"),
        color=alt.Color("company:N", title="Company"),
    )
    .properties(title="Monthly Stock Prices", width=600, height=400)
)

# Save as self-contained HTML
chart.save("/home/user/myproject/chart.html")
print("Chart saved to /home/user/myproject/chart.html")