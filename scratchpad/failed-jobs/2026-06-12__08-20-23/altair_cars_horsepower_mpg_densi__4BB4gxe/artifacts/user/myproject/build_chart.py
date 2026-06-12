import altair as alt
from vega_datasets import data

# Build a 2D binned bubble density plot
chart = (
    alt.Chart(data.cars.url)
    .mark_circle()
    .encode(
        x=alt.X("Horsepower:Q", bin=alt.Bin(maxbins=10)),
        y=alt.Y("Miles_per_Gallon:Q", bin=alt.Bin(maxbins=10)),
        size=alt.Size(aggregate="count", type="quantitative"),
        color=alt.Color("Acceleration:Q", aggregate="mean", scale=alt.Scale(scheme="viridis")),
    )
    .properties(
        width=400,
        height=300,
        title="Cars Horsepower vs MPG Density",
    )
)

chart.save("/home/user/myproject/chart.html")