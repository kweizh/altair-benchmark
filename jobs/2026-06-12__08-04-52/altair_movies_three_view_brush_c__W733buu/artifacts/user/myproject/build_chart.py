import altair as alt
from vega_datasets import data

source = data.movies.url

brush = alt.selection_interval(name="brush")

# Base chart with IMDB_Rating null filter
base = alt.Chart(source).transform_filter(
    alt.datum.IMDB_Rating != None
)

# View A: Scatter plot
# Additionally excludes null Rotten_Tomatoes_Rating
scatter = base.transform_filter(
    alt.datum.Rotten_Tomatoes_Rating != None
).mark_point().encode(
    x='IMDB_Rating:Q',
    y='Rotten_Tomatoes_Rating:Q',
    color=alt.condition(brush, 'Major_Genre:N', alt.value('lightgray'))
).add_params(brush)

# View B: Genre bar chart
bar = base.transform_joinaggregate(
    total='count()',
    groupby=['Major_Genre']
).transform_window(
    rank='dense_rank()',
    sort=[alt.SortField('total', order='descending')],
    groupby=[]
).transform_filter(
    alt.datum.rank <= 8
).transform_filter(
    brush
).mark_bar().encode(
    x='Major_Genre:N',
    y='count():Q'
)

# View C: Rating histogram
histogram = base.transform_filter(
    brush
).mark_bar().encode(
    x=alt.X('IMDB_Rating:Q', bin=alt.Bin(maxbins=20)),
    y='count():Q'
)

# Compose the dashboard
dashboard = scatter & (bar | histogram)

# Save to HTML
dashboard.save('/home/user/myproject/chart.html')
