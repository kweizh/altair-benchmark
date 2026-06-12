import altair as alt

# Use the CDN URL for the penguins dataset directly
# (equivalent to vega_datasets.data.penguins.url in newer versions)
source = "https://cdn.jsdelivr.net/npm/vega-datasets/data/penguins.json"

chart = (
    alt.Chart(source)
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

chart.save("/home/user/myproject/chart.html")