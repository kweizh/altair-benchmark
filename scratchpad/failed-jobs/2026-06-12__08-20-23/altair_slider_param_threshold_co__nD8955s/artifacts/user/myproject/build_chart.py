import altair as alt
from vega_datasets import data

# Create a range slider binding for the horsepower threshold
hp_slider = alt.binding_range(
    min=50,
    max=250,
    step=10,
    name="HP threshold: ",
)

# Create a top-level parameter bound to the slider, initial value 150
hp_threshold = alt.param(value=150, bind=hp_slider)

# Build the scatter plot
chart = (
    alt.Chart(data.cars.url)
    .mark_point()
    .encode(
        x="Horsepower:Q",
        y="Miles_per_Gallon:Q",
        color=alt.condition(
            alt.datum.Horsepower < hp_threshold,
            alt.value("steelblue"),
            alt.value("orange"),
        ),
    )
    .add_params(hp_threshold)
    .properties(title="MPG vs Horsepower (threshold)")
)

# Save as self-contained HTML
chart.save("/home/user/myproject/chart.html")