import altair as alt
from vega_datasets import data

# URL-based data source (types declared explicitly in encoding shorthands)
source = data.cars.url

# Slider binding: min=50, max=250, step=10, label exactly "HP threshold: "
slider = alt.binding_range(min=50, max=250, step=10, name="HP threshold: ")

# Top-level parameter with initial value 150, bound to the slider
hp_threshold = alt.param(value=150, bind=slider)

# Conditional color: steelblue when datum.Horsepower < threshold, else orange
color_encoding = (
    alt.when(alt.datum.Horsepower < hp_threshold)
    .then(alt.value("steelblue"))
    .otherwise(alt.value("orange"))
)

chart = (
    alt.Chart(source)
    .mark_point()
    .encode(
        x="Horsepower:Q",
        y="Miles_per_Gallon:Q",
        color=color_encoding,
    )
    .properties(title="MPG vs Horsepower (threshold)")
    .add_params(hp_threshold)
)

chart.save("chart.html")
print("Saved chart.html")
