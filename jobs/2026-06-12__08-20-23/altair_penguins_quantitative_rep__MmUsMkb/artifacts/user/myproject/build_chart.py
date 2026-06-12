import altair as alt
from vega_datasets import data

# Build the base chart using the penguins URL data source
base = (
    alt.Chart(data.penguins.url)
    .mark_point()
    .encode(
        x=alt.X(alt.repeat("column"), type="quantitative", scale=alt.Scale(zero=False)),
        y=alt.Y(alt.repeat("row"), type="quantitative", scale=alt.Scale(zero=False)),
        color=alt.Color("Species:N"),
    )
    .properties(
        width=180,
        height=180,
    )
)

# Create the 2x2 SPLOM via repeat
chart = base.repeat(
    row=["Body Mass (g)", "Flipper Length (mm)"],
    column=["Beak Length (mm)", "Beak Depth (mm)"],
)

# Save as self-contained HTML
chart.save("/home/user/myproject/chart.html")