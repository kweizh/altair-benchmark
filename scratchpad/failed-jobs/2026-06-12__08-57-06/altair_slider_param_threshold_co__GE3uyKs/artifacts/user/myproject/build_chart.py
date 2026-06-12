import altair as alt
from vega_datasets import data

# Build the slider binding and threshold parameter
slider = alt.binding_range(min=50, max=250, step=10, name="HP threshold: ")
threshold = alt.param(value=150, bind=slider)

# Build the scatter plot
chart = (
    alt.Chart(data.cars.url)
    .mark_point()
    .encode(
        x=alt.X("Horsepower:Q"),
        y=alt.Y("Miles_per_Gallon:Q"),
        color=alt.when(alt.datum.Horsepower < threshold)
        .then(alt.value("steelblue"))
        .otherwise(alt.value("orange")),
    )
    .add_params(threshold)
    .properties(title="MPG vs Horsepower (threshold)")
)

chart.save("/home/user/myproject/chart.html")
