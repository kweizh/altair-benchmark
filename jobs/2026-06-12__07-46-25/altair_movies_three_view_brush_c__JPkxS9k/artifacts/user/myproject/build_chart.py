import altair as alt
from vega_datasets import data

def build_dashboard():
    # Define the 2D interval selection (brush)
    brush = alt.selection_interval(name="brush")

    # 1. View A (scatter plot, brush host)
    # x: IMDB_Rating, y: Rotten_Tomatoes_Rating
    # Points inside the brush are colored by Major_Genre, points outside are colored 'lightgray'
    scatter = alt.Chart(data.movies.url).mark_point().encode(
        x=alt.X('IMDB_Rating:Q', title='IMDb Rating'),
        y=alt.Y('Rotten_Tomatoes_Rating:Q', title='Rotten Tomatoes Rating'),
        color=alt.when(brush).then('Major_Genre:N').otherwise(alt.value('lightgray'))
    ).add_params(
        brush
    ).transform_filter(
        alt.datum.IMDB_Rating != None
    ).transform_filter(
        alt.datum.Rotten_Tomatoes_Rating != None
    ).properties(
        width=600,
        height=300,
        title="IMDb vs. Rotten Tomatoes Movie Ratings"
    )

    # 2. View B (genre bar chart)
    # Bar chart of count() by Major_Genre, filtered through the brush.
    # We restrict to the top 8 most frequent Major_Genre values globally.
    bar = alt.Chart(data.movies.url).mark_bar().encode(
        x=alt.X('count():Q', title='Count'),
        y=alt.Y('Major_Genre:N', sort='-x', title='Major Genre')
    ).transform_filter(
        alt.datum.IMDB_Rating != None
    ).transform_filter(
        alt.datum.Major_Genre != None
    ).transform_joinaggregate(
        genre_count='count()',
        groupby=['Major_Genre']
    ).transform_window(
        genre_rank='dense_rank()',
        sort=[alt.SortField('genre_count', order='descending')]
    ).transform_filter(
        alt.datum.genre_rank <= 8
    ).transform_filter(
        brush
    ).properties(
        width=260,
        height=250,
        title="Top 8 Genres (Filtered by Brush)"
    )

    # 3. View C (rating histogram)
    # Histogram of IMDB_Rating (bin maxbins=20) with count(), filtered through the brush.
    hist = alt.Chart(data.movies.url).mark_bar().encode(
        x=alt.X('IMDB_Rating:Q', bin=alt.Bin(maxbins=20), title='IMDb Rating'),
        y=alt.Y('count():Q', title='Count')
    ).transform_filter(
        alt.datum.IMDB_Rating != None
    ).transform_filter(
        brush
    ).properties(
        width=260,
        height=250,
        title="IMDb Rating Distribution (Filtered by Brush)"
    )

    # Compose the layout: scatter on top, bar and histogram side-by-side underneath
    dashboard = scatter & (bar | hist)

    # Save the dashboard as a self-contained HTML file
    dashboard.save('/home/user/myproject/chart.html')
    print("Dashboard successfully saved to /home/user/myproject/chart.html")

if __name__ == "__main__":
    build_dashboard()
