import altair as alt

# The Palmer Penguins dataset URL from vega-datasets
source = "https://raw.githubusercontent.com/vega/vega-datasets/master/data/penguins.json"

# The four quantitative features for the SPLOM
features = [
    "Beak Length (mm)",
    "Beak Depth (mm)",
    "Flipper Length (mm)",
    "Body Mass (g)",
]

# Create the interval selection brush (global resolve by default)
brush = alt.selection_interval(encodings=["x", "y"])

# Build the base chart with point marks
chart = (
    alt.Chart(source)
    .mark_point()
    .encode(
        x=alt.X(alt.repeat("column"), type="quantitative", scale=alt.Scale(zero=False)),
        y=alt.Y(alt.repeat("row"), type="quantitative", scale=alt.Scale(zero=False)),
        color=alt.condition(brush, "Species:N", alt.value("lightgray")),
    )
    .add_params(brush)
    .repeat(row=features, column=features)
)

# Save to self-contained HTML
chart.save("/home/user/myproject/chart.html")
