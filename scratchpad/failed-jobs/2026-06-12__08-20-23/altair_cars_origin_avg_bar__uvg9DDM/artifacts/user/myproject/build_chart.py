import altair as alt
from vega_datasets import data

# Build a single bar chart: mean MPG by Origin, sorted descending
chart = (
    alt.Chart(data.cars.url)
    .mark_bar()
    .encode(
        x=alt.X("Origin:N").sort(
            field="Miles_per_Gallon", op="mean", order="descending"
        ),
        y=alt.Y("mean(Miles_per_Gallon):Q"),
        tooltip=[
            alt.Tooltip("mean(Miles_per_Gallon):Q", title="Mean MPG"),
            alt.Tooltip("count():Q", title="Number of Cars"),
        ],
    )
)

# Save as self-contained HTML
chart.save("/home/user/myproject/chart.html")