import altair as alt
from vega_datasets import data

def build_chart():
    # Load the movies dataset URL
    movies_url = data.movies.url

    # Create the interval selection (2D brush) projected onto x and y
    brush = alt.selection_interval(encodings=['x', 'y'])

    # Heatmap configuration
    # IMDB_Rating on x, Rotten_Tomatoes_Rating on y, both binned with maxbins=20
    heatmap = alt.Chart(movies_url).mark_rect().encode(
        x=alt.X('IMDB_Rating:Q', bin=alt.Bin(maxbins=20), title='IMDB Rating', axis=alt.Axis(minExtent=40)),
        y=alt.Y('Rotten_Tomatoes_Rating:Q', bin=alt.Bin(maxbins=20), title='Rotten Tomatoes Rating', axis=alt.Axis(minExtent=60)),
        color=alt.Color('count():Q').scale(scheme='viridis').title('Count')
    ).properties(
        width=400,
        height=400
    ).add_params(
        brush
    )

    # Top marginal histogram (IMDB_Rating)
    # Baseline gray bar showing total count
    top_background = alt.Chart(movies_url).mark_bar(color='lightgray').encode(
        x=alt.X('IMDB_Rating:Q', bin=alt.Bin(maxbins=20), title=None, axis=alt.Axis(labels=False, ticks=False)),
        y=alt.Y('count():Q', title='Count', axis=alt.Axis(minExtent=60))
    )

    # Filtered colored bar on top reacting to the brush
    top_foreground = alt.Chart(movies_url).mark_bar(color='steelblue').encode(
        x=alt.X('IMDB_Rating:Q', bin=alt.Bin(maxbins=20), title=None, axis=alt.Axis(labels=False, ticks=False)),
        y=alt.Y('count():Q', title='Count', axis=alt.Axis(minExtent=60))
    ).transform_filter(
        brush
    )

    # Layer top marginal histogram
    top_histogram = alt.layer(top_background, top_foreground).properties(
        width=400,
        height=80
    )

    # Right marginal histogram (Rotten_Tomatoes_Rating)
    # Baseline gray bar showing total count
    right_background = alt.Chart(movies_url).mark_bar(color='lightgray').encode(
        x=alt.X('count():Q', title='Count', axis=alt.Axis(minExtent=40)),
        y=alt.Y('Rotten_Tomatoes_Rating:Q', bin=alt.Bin(maxbins=20), title=None, axis=alt.Axis(labels=False, ticks=False))
    )

    # Filtered colored bar on top reacting to the brush
    right_foreground = alt.Chart(movies_url).mark_bar(color='steelblue').encode(
        x=alt.X('count():Q', title='Count', axis=alt.Axis(minExtent=40)),
        y=alt.Y('Rotten_Tomatoes_Rating:Q', bin=alt.Bin(maxbins=20), title=None, axis=alt.Axis(labels=False, ticks=False))
    ).transform_filter(
        brush
    )

    # Layer right marginal histogram
    right_histogram = alt.layer(right_background, right_foreground).properties(
        width=80,
        height=400
    )

    # Compose the compound chart using horizontal and vertical concatenation
    # Center: heatmap, Right: right_histogram (horizontally concatenated)
    # Top: top_histogram (vertically concatenated on top of the row)
    chart = alt.vconcat(
        top_histogram,
        alt.hconcat(heatmap, right_histogram, spacing=5),
        spacing=5
    )

    # Save the final compound chart as HTML
    chart.save('/home/user/myproject/chart.html')
    print("Chart saved successfully to /home/user/myproject/chart.html")

if __name__ == '__main__':
    build_chart()
