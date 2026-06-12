import altair as alt
from vega_datasets import data

def build_chart():
    # Use data.movies.url as the data source
    chart = alt.Chart(data.movies.url).mark_bar().encode(
        x=alt.X('IMDB_Rating:Q').bin(step=0.5),
        y='count()'
    ).transform_filter(
        alt.datum.IMDB_Rating != None
    ).properties(
        title="IMDB Rating Distribution"
    )
    
    # Save chart as HTML
    chart.save("chart.html")

if __name__ == "__main__":
    build_chart()
