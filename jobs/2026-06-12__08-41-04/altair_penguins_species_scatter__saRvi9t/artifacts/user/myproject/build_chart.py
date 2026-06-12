import altair as alt

# The installed vega_datasets (0.9.0) pre-dates the penguins dataset.
# Use the canonical URL from the vega-datasets project directly.
penguins_url = (
    "https://cdn.jsdelivr.net/npm/vega-datasets@v1.31.1/data/penguins.json"
)

chart = (
    alt.Chart(penguins_url)
    .mark_point(filled=True, size=80)
    .encode(
        x=alt.X("Flipper Length (mm):Q", scale=alt.Scale(zero=False)),
        y=alt.Y("Body Mass (g):Q", scale=alt.Scale(zero=False)),
        color=alt.Color("Species:N"),
        shape=alt.Shape("Sex:N"),
        tooltip=[
            "Species:N",
            "Island:N",
            "Flipper Length (mm):Q",
            "Body Mass (g):Q",
        ],
    )
    .interactive()
)

chart.save("chart.html")
print("Saved chart.html")
