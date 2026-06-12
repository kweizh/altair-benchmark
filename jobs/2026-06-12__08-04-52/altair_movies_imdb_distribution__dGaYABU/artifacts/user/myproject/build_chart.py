import altair as alt
from vega_datasets import data

source = data.movies.url

chart = alt.Chart(source).mark_bar().encode(
    x=alt.X('IMDB_Rating:Q', bin=alt.Bin(step=0.5)),
    y='count()'
).transform_filter(
    alt.datum.IMDB_Rating != None
).properties(
    title="IMDB Rating Distribution"
)

chart.save("chart.html")
