"""
Three-view crossfilter dashboard for the movies dataset.

Layout:
    scatter (View A)
    ─────────────────────────
    bar chart (B) | histogram (C)

Dragging a 2-D brush over the scatter plot filters both lower views.
"""

import altair as alt
from vega_datasets import data

# ── data source (URL-based; types declared inline) ──────────────────────────
movies_url = data.movies.url
source = alt.UrlData(url=movies_url)

# ── shared brush (interval / 2-D selection) ──────────────────────────────────
brush = alt.selection_interval(name="brush")

# ── null-filter expressions ──────────────────────────────────────────────────
not_null_imdb = alt.datum.IMDB_Rating != None          # noqa: E711
not_null_rt   = alt.datum.Rotten_Tomatoes_Rating != None  # noqa: E711

# ── top-8 genre ranking helpers (applied to View B) ──────────────────────────
# Compute count per genre, rank descending, keep rank ≤ 8.
top8_filter = alt.datum.genre_rank <= 8

# ── View A – scatter plot (brush host) ──────────────────────────────────────
scatter = (
    alt.Chart(source)
    .mark_point(filled=True, opacity=0.6, size=40)
    .transform_filter(not_null_imdb)
    .transform_filter(not_null_rt)
    .encode(
        x=alt.X("IMDB_Rating:Q",
                 scale=alt.Scale(domain=[0, 10]),
                 title="IMDB Rating"),
        y=alt.Y("Rotten_Tomatoes_Rating:Q",
                 scale=alt.Scale(domain=[0, 100]),
                 title="Rotten Tomatoes Rating"),
        color=alt.when(brush)
             .then(alt.Color("Major_Genre:N", legend=alt.Legend(title="Genre")))
             .otherwise(alt.value("lightgray")),
        tooltip=[
            alt.Tooltip("Title:N"),
            alt.Tooltip("IMDB_Rating:Q"),
            alt.Tooltip("Rotten_Tomatoes_Rating:Q"),
            alt.Tooltip("Major_Genre:N"),
        ],
    )
    .add_params(brush)
    .properties(
        width=600,
        height=350,
        title="IMDB Rating vs Rotten Tomatoes Rating",
    )
)

# ── View B – genre bar chart (filtered by brush) ─────────────────────────────
# The brush filter is placed BEFORE the aggregate so the genre counts reflect
# only the rows inside the current brush selection.
bar = (
    alt.Chart(source)
    .mark_bar(color="steelblue")
    .transform_filter(not_null_imdb)
    .transform_filter(brush)                    # ← crossfilter
    .transform_aggregate(
        genre_count="count()",
        groupby=["Major_Genre"],
    )
    .transform_window(
        genre_rank="rank(genre_count)",
        sort=[alt.SortField("genre_count", order="descending")],
    )
    .transform_filter(top8_filter)
    .encode(
        x=alt.X("genre_count:Q", title="Count"),
        y=alt.Y("Major_Genre:N",
                 sort=alt.EncodingSortField(field="genre_count",
                                            order="descending"),
                 title="Genre"),
        tooltip=[
            alt.Tooltip("Major_Genre:N", title="Genre"),
            alt.Tooltip("genre_count:Q", title="Count"),
        ],
    )
    .properties(
        width=290,
        height=280,
        title="Movies by Genre (brush-filtered)",
    )
)

# ── View C – IMDB Rating histogram (filtered by brush) ───────────────────────
histogram = (
    alt.Chart(source)
    .mark_bar(color="salmon")
    .transform_filter(not_null_imdb)
    .transform_filter(brush)                    # ← crossfilter
    .encode(
        x=alt.X("IMDB_Rating:Q",
                 bin=alt.Bin(maxbins=20),
                 title="IMDB Rating"),
        y=alt.Y("count():Q", title="Count"),
        tooltip=[
            alt.Tooltip("IMDB_Rating:Q", bin=alt.Bin(maxbins=20),
                         title="Rating bin"),
            alt.Tooltip("count():Q", title="Count"),
        ],
    )
    .properties(
        width=290,
        height=280,
        title="IMDB Rating Distribution (brush-filtered)",
    )
)

# ── Compose dashboard ─────────────────────────────────────────────────────────
dashboard = scatter & (bar | histogram)

dashboard = dashboard.properties(
    title=alt.TitleParams(
        text="Movies Crossfilter Dashboard",
        subtitle="Drag a brush on the scatter plot to filter the charts below",
        fontSize=18,
        subtitleFontSize=13,
        anchor="middle",
    )
)

# ── Export ────────────────────────────────────────────────────────────────────
out_path = "/home/user/myproject/chart.html"
dashboard.save(out_path)
print(f"Dashboard saved → {out_path}")
