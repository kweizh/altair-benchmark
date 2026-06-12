import altair as alt
from vega_datasets import data

chart = (
    alt.Chart(data.cars.url)
    .mark_circle()
    .encode(
        x=alt.X("Horsepower:Q", bin=alt.Bin(maxbins=10)),
        y=alt.Y("Miles_per_Gallon:Q", bin=alt.Bin(maxbins=10)),
        size=alt.Size("count():Q"),
        color=alt.Color(
            "mean(Acceleration):Q",
            scale=alt.Scale(scheme="viridis"),
        ),
    )
    .properties(
        width=400,
        height=300,
        title="Cars Horsepower vs MPG Density",
    )
)

chart.save("chart.html")
print("chart.html written successfully.")
