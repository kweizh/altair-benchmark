import altair as alt
from vega_datasets import data

# Use URL-based data source
source = data.movies.url

# Build the histogram chart
chart = (
    alt.Chart(source)
    .mark_bar()
    .encode(
        x=alt.X("IMDB_Rating:Q").bin(step=0.5),
        y="count()",
    )
    .transform_filter(alt.datum.IMDB_Rating != None)
    .properties(title="IMDB Rating Distribution")
)

# Save as self-contained HTML
chart.save("chart.html")