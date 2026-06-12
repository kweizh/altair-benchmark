import altair as alt
from vega_datasets import data

# Build a binned histogram of petalLength colored by species
chart = alt.Chart(data.iris.url).mark_bar().encode(
    x=alt.X("petalLength:Q", bin=alt.BinParams(maxbins=20)),
    y="count()",
    color="species:N",
)

# Save as a self-contained HTML file
chart.save("/home/user/myproject/chart.html")