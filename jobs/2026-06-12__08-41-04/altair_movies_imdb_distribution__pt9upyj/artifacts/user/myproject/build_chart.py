import altair as alt
from vega_datasets import data

chart = (
    alt.Chart(data.movies.url)
    .mark_bar()
    .transform_filter(alt.datum.IMDB_Rating != None)
    .encode(
        x=alt.X("IMDB_Rating:Q").bin(step=0.5),
        y="count()",
    )
    .properties(title="IMDB Rating Distribution")
)

chart.save("chart.html")
print("Saved chart.html")
