import altair as alt
from vega_datasets import data

# ── Data source (URL-based, so declare types explicitly) ──────────────
source = data.movies.url

# ── Shared interval selection (the crossfilter brush) ─────────────────
brush = alt.selection_interval()

# ── Common null-filter transforms ─────────────────────────────────────
# Every view must exclude rows where IMDB_Rating is null.
# The scatter view additionally excludes null Rotten_Tomatoes_Rating.
filter_imdb_not_null = alt.datum.IMDB_Rating != None
filter_rt_not_null = alt.datum.Rotten_Tomatoes_Rating != None

# ── View A: Scatter plot (brush host) ────────────────────────────────
scatter = (
    alt.Chart(source)
    .mark_point()
    .transform_filter(filter_imdb_not_null)
    .transform_filter(filter_rt_not_null)
    .encode(
        x=alt.X("IMDB_Rating:Q"),
        y=alt.Y("Rotten_Tomatoes_Rating:Q"),
        color=alt.condition(
            brush,
            alt.Color("Major_Genre:N"),
            alt.value("lightgray"),
        ),
    )
    .add_params(brush)
    .properties(width=600, height=400)
)

# ── View B: Genre bar chart (top-8 genres, filtered by brush) ────────
# First, compute the top-8 most frequent Major_Genre values.
# We build a lookup of top genres via aggregate + window + filter,
# then join it back to the main data and filter on rank <= 8.

bar = (
    alt.Chart(source)
    .mark_bar()
    .transform_filter(filter_imdb_not_null)
    # Apply the brush crossfilter
    .transform_filter(brush)
    # Compute genre counts, rank them, and keep only top 8
    .transform_aggregate(count="count()", groupby=["Major_Genre"])
    .transform_window(rank="rank(count)", sort=[alt.SortField("count", order="descending")])
    .transform_filter(alt.datum.rank <= 8)
    .encode(
        x=alt.X("count():Q"),
        y=alt.Y("Major_Genre:N", sort="-x"),
    )
    .properties(width=300, height=400)
)

# ── View C: IMDB_Rating histogram (filtered by brush) ────────────────
histogram = (
    alt.Chart(source)
    .mark_bar()
    .transform_filter(filter_imdb_not_null)
    # Apply the brush crossfilter
    .transform_filter(brush)
    .encode(
        x=alt.X("IMDB_Rating:Q", bin=alt.Bin(maxbins=20)),
        y=alt.Y("count():Q"),
    )
    .properties(width=300, height=400)
)

# ── Compose the dashboard: scatter on top, bar | histogram below ─────
dashboard = scatter & (bar | histogram)

# ── Save as self-contained HTML ──────────────────────────────────────
dashboard.save("/home/user/myproject/chart.html")