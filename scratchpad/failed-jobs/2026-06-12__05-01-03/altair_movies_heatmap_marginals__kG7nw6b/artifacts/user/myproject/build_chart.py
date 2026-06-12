"""
Build a 2D binned heatmap with marginal histograms for movies data.

Layout:
  [ top_hist           ]
  [ heatmap  | right_hist ]

The heatmap has a 2D interval brush; both marginals react to it by
showing a filtered (coloured) bar layer on top of a baseline grey bar.
"""

import altair as alt
from vega_datasets import data

# ── data source ──────────────────────────────────────────────────────────────
movies_url = data.movies.url          # CDN URL – keeps the chart self-contained

# ── brush selection (2D interval on both x and y) ────────────────────────────
brush = alt.selection_interval(
    name="brush",
    encodings=["x", "y"],
    empty=True,
)

# ── colour palette for the filtered bars ─────────────────────────────────────
FILTER_COLOR = "#f58518"

# ─────────────────────────────────────────────────────────────────────────────
# 1.  CENTER: 2D binned heatmap
# ─────────────────────────────────────────────────────────────────────────────
heatmap = (
    alt.Chart(movies_url)
    .mark_rect()
    .encode(
        x=alt.X(
            "IMDB_Rating:Q",
            bin=alt.Bin(maxbins=20),
            axis=alt.Axis(title="IMDB Rating"),
        ),
        y=alt.Y(
            "Rotten_Tomatoes_Rating:Q",
            bin=alt.Bin(maxbins=20),
            axis=alt.Axis(title="Rotten Tomatoes Rating"),
        ),
        color=alt.Color(
            "count():Q",
            scale=alt.Scale(scheme="viridis"),
            legend=alt.Legend(title="Count"),
        ),
    )
    .add_params(brush)
    .properties(width=400, height=400)
)

# ─────────────────────────────────────────────────────────────────────────────
# 2.  TOP: marginal histogram of IMDB_Rating
#     – baseline grey bar (total) + filtered coloured bar on top
# ─────────────────────────────────────────────────────────────────────────────
imdb_bin = alt.X(
    "IMDB_Rating:Q",
    bin=alt.Bin(maxbins=20),
    axis=alt.Axis(title=""),
)

top_base = (
    alt.Chart(movies_url)
    .mark_bar(color="lightgray", opacity=0.6)
    .encode(
        x=imdb_bin,
        y=alt.Y("count():Q", axis=alt.Axis(title="Count")),
    )
)

top_filtered = (
    alt.Chart(movies_url)
    .mark_bar(color=FILTER_COLOR, opacity=0.8)
    .encode(
        x=imdb_bin,
        y=alt.Y("count():Q"),
    )
    .transform_filter(brush)
)

top_hist = (
    alt.layer(top_base, top_filtered)
    .properties(width=400, height=120)
)

# ─────────────────────────────────────────────────────────────────────────────
# 3.  RIGHT: marginal histogram of Rotten_Tomatoes_Rating
#     – horizontal bars (count on x, binned rating on y)
# ─────────────────────────────────────────────────────────────────────────────
rt_bin = alt.Y(
    "Rotten_Tomatoes_Rating:Q",
    bin=alt.Bin(maxbins=20),
    axis=alt.Axis(title=""),
)

right_base = (
    alt.Chart(movies_url)
    .mark_bar(color="lightgray", opacity=0.6)
    .encode(
        y=rt_bin,
        x=alt.X("count():Q", axis=alt.Axis(title="Count")),
    )
)

right_filtered = (
    alt.Chart(movies_url)
    .mark_bar(color=FILTER_COLOR, opacity=0.8)
    .encode(
        y=rt_bin,
        x=alt.X("count():Q"),
    )
    .transform_filter(brush)
)

right_hist = (
    alt.layer(right_base, right_filtered)
    .properties(width=120, height=400)
)

# ─────────────────────────────────────────────────────────────────────────────
# 4.  Compose: top / (heatmap | right)
# ─────────────────────────────────────────────────────────────────────────────
bottom_row = alt.hconcat(heatmap, right_hist, spacing=5)
chart = alt.vconcat(top_hist, bottom_row, spacing=5).properties(
    title=alt.TitleParams(
        text="Movies: IMDB vs Rotten Tomatoes Rating",
        subtitle="Drag on the heatmap to filter the marginal histograms",
        anchor="middle",
        fontSize=18,
        subtitleFontSize=13,
    )
)

# ─────────────────────────────────────────────────────────────────────────────
# 5.  Save
# ─────────────────────────────────────────────────────────────────────────────
output_path = "/home/user/myproject/chart.html"
chart.save(output_path)
print(f"Chart saved → {output_path}")
