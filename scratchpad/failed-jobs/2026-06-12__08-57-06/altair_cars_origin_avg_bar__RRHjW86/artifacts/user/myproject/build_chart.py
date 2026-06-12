import altair as alt
from vega_datasets import data

chart = (
    alt.Chart(data.cars.url)
    .mark_bar()
    .encode(
        x=alt.X("Origin:N", sort=alt.EncodingSortField(
            field="Miles_per_Gallon", op="mean", order="descending"
        )),
        y=alt.Y("mean(Miles_per_Gallon):Q"),
        tooltip=[
            alt.Tooltip("mean(Miles_per_Gallon):Q", format=".1f"),
            alt.Tooltip("count():Q"),
        ],
    )
)

chart.save("/home/user/myproject/chart.html")
print("chart.html saved successfully")
