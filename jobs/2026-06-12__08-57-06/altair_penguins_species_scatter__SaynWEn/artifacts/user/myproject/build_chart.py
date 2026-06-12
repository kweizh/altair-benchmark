import altair as alt

PENGUINS_URL = "https://raw.githubusercontent.com/vega/vega-datasets/main/data/penguins.json"

chart = (
    alt.Chart(PENGUINS_URL)
    .mark_point(filled=True, size=80)
    .encode(
        x=alt.X("Flipper Length (mm):Q").scale(zero=False),
        y=alt.Y("Body Mass (g):Q").scale(zero=False),
        color=alt.Color("Species:N"),
        shape=alt.Shape("Sex:N"),
        tooltip=[
            alt.Tooltip("Species:N"),
            alt.Tooltip("Island:N"),
            alt.Tooltip("Flipper Length (mm):Q"),
            alt.Tooltip("Body Mass (g):Q"),
        ],
    )
    .interactive()
)

chart.save("/home/user/myproject/chart.html")
