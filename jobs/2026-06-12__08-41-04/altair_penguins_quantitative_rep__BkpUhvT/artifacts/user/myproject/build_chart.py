import altair as alt
from vega_datasets import data

# data.penguins.url is available in newer vega_datasets; fall back to the
# canonical CDN path if this version of the library does not include it.
try:
    penguins_url = data.penguins.url
except AttributeError:
    penguins_url = "https://cdn.jsdelivr.net/npm/vega-datasets/data/penguins.json"

chart = (
    alt.Chart(penguins_url)
    .mark_point()
    .encode(
        x=alt.X(
            alt.repeat("column"),
            type="quantitative",
            scale=alt.Scale(zero=False),
        ),
        y=alt.Y(
            alt.repeat("row"),
            type="quantitative",
            scale=alt.Scale(zero=False),
        ),
        color=alt.Color("Species:N"),
    )
    .properties(width=180, height=180)
    .repeat(
        row=["Body Mass (g)", "Flipper Length (mm)"],
        column=["Beak Length (mm)", "Beak Depth (mm)"],
    )
)

chart.save("chart.html")
print("Saved chart.html")
