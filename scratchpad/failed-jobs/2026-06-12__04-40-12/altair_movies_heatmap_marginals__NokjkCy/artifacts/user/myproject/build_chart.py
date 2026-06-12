import altair as alt
from vega_datasets import data

source = data.movies.url

brush = alt.selection_interval(encodings=['x', 'y'])

heatmap = alt.Chart(source).mark_rect().encode(
    x=alt.X('IMDB_Rating:Q', bin=alt.Bin(maxbins=20)),
    y=alt.Y('Rotten_Tomatoes_Rating:Q', bin=alt.Bin(maxbins=20)),
    color=alt.Color('count():Q', scale=alt.Scale(scheme='viridis'))
).add_params(
    brush
).properties(
    width=400,
    height=400
)

base_top = alt.Chart(source).mark_bar(color='gray').encode(
    x=alt.X('IMDB_Rating:Q', bin=alt.Bin(maxbins=20), title=''),
    y=alt.Y('count():Q', title='Count')
)

filtered_top = alt.Chart(source).mark_bar(color='steelblue').encode(
    x=alt.X('IMDB_Rating:Q', bin=alt.Bin(maxbins=20), title=''),
    y=alt.Y('count():Q', title='Count')
).transform_filter(
    brush
)

top_hist = (base_top + filtered_top).properties(
    width=400,
    height=100
)

base_right = alt.Chart(source).mark_bar(color='gray').encode(
    y=alt.Y('Rotten_Tomatoes_Rating:Q', bin=alt.Bin(maxbins=20), title=''),
    x=alt.X('count():Q', title='Count')
)

filtered_right = alt.Chart(source).mark_bar(color='steelblue').encode(
    y=alt.Y('Rotten_Tomatoes_Rating:Q', bin=alt.Bin(maxbins=20), title=''),
    x=alt.X('count():Q', title='Count')
).transform_filter(
    brush
)

right_hist = (base_right + filtered_right).properties(
    width=100,
    height=400
)

chart = top_hist & (heatmap | right_hist)
chart = chart.configure_view(strokeWidth=0)

chart.save('/home/user/myproject/chart.html')
