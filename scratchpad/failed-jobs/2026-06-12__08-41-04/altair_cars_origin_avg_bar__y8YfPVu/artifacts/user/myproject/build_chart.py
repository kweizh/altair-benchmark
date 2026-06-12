import altair as alt
from vega_datasets import data

chart = (
    alt.Chart(data.cars.url)
    .mark_bar()
    .encode(
        x=alt.X("Origin:N").sort(field="Miles_per_Gallon", op="mean", order="descending"),
        y=alt.Y("mean(Miles_per_Gallon):Q"),
        tooltip=[
            alt.Tooltip("mean(Miles_per_Gallon):Q", title="Mean MPG"),
            alt.Tooltip("count():Q", title="Number of Cars"),
        ],
    )
)

chart.save("chart.html")
print("Saved chart.html")
