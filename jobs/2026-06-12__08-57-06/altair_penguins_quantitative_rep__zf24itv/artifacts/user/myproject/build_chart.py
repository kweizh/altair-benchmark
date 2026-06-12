import altair as alt

PENGUINS_URL = "https://raw.githubusercontent.com/vega/vega-datasets/main/data/penguins.json"

base = (
    alt.Chart(PENGUINS_URL)
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
        color="Species:N",
    )
    .properties(width=180, height=180)
)

chart = base.repeat(
    row=["Body Mass (g)", "Flipper Length (mm)"],
    column=["Beak Length (mm)", "Beak Depth (mm)"],
)

chart.save("/home/user/myproject/chart.html")
