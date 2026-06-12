import altair as alt
from vega_datasets import data

# ── Data source ──────────────────────────────────────────────────────────────
source = data.movies.url

# ── Brush selection ──────────────────────────────────────────────────────────
brush = alt.selection_interval(name="brush")

# ── Conditional color for scatter (brushed = genre color, else lightgray) ────
color_cond = alt.condition(brush, "Major_Genre:N", alt.value("lightgray"))

# ── View A: Scatter plot (brush host) ────────────────────────────────────────
scatter = (
    alt.Chart(source)
    .mark_point()
    .encode(
        alt.X("IMDB_Rating:Q", title="IMDB Rating"),
        alt.Y("Rotten_Tomatoes_Rating:Q", title="Rotten Tomatoes Rating"),
        alt.ColorValue(
            condition=color_cond["condition"],
            value=color_cond["value"],
        ),
    )
    .transform_filter(alt.datum.IMDB_Rating != None)  # noqa: E711
    .transform_filter(alt.datum.Rotten_Tomatoes_Rating != None)  # noqa: E711
    .add_params(brush)
    .properties(title="IMDB vs Rotten Tomatoes Ratings")
)

# ── View B: Genre bar chart (top-8, filtered through brush) ──────────────────
bar = (
    alt.Chart(source)
    .mark_bar()
    .encode(
        alt.X("Major_Genre:N", title="Genre"),
        alt.Y("count()", title="Count"),
    )
    .transform_filter(alt.datum.IMDB_Rating != None)  # noqa: E711
    .transform_filter(brush)
    .transform_aggregate(count="count()", groupby=["Major_Genre"])
    .transform_window(
        rank="rank(count)", sort=[alt.SortField("count", order="descending")]
    )
    .transform_filter(alt.datum.rank <= 8)
    .properties(title="Top 8 Genres (brushed)")
)

# ── View C: IMDB Rating histogram (filtered through brush) ───────────────────
hist = (
    alt.Chart(source)
    .mark_bar()
    .encode(
        alt.X("IMDB_Rating:Q", bin=alt.Bin(maxbins=20), title="IMDB Rating"),
        alt.Y("count()", title="Count"),
    )
    .transform_filter(alt.datum.IMDB_Rating != None)  # noqa: E711
    .transform_filter(brush)
    .properties(title="IMDB Rating Distribution (brushed)")
)

# ── Compose dashboard: scatter on top, bar | histogram below ─────────────────
dashboard = alt.vconcat(
    scatter,
    alt.hconcat(bar, hist),
).resolve_scale(color="independent")

# ── Save self-contained HTML ─────────────────────────────────────────────────
output_path = "/home/user/myproject/chart.html"
dashboard.save(output_path)
print(f"Dashboard saved to {output_path}")
