import altair as alt
from vega_datasets import data

chart = (
    alt.Chart(data.iris.url)
    .mark_bar()
    .encode(
        x=alt.X("petalLength:Q", bin=alt.Bin(maxbins=20), title="Petal Length"),
        y=alt.Y("count()", title="Count"),
        color=alt.Color("species:N", title="Species"),
    )
)

chart.save("/home/user/myproject/chart.html")
