import altair as alt
from vega_datasets import data

chart = (
    alt.Chart(data.cars.url)
    .mark_circle()
    .encode(
        alt.X("Horsepower:Q", bin=alt.Bin(maxbins=10)),
        alt.Y("Miles_per_Gallon:Q", bin=alt.Bin(maxbins=10)),
        alt.Size("count()"),
        alt.Color("mean(Acceleration):Q", scale=alt.Scale(scheme="viridis")),
    )
    .properties(width=400, height=300, title="Cars Horsepower vs MPG Density")
)

chart.save("/home/user/myproject/chart.html")
print("chart.html saved successfully")
