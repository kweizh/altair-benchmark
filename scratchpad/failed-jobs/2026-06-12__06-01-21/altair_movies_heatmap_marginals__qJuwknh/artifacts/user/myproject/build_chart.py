import altair as alt
from vega_datasets import data

# ── Data source ──────────────────────────────────────────────────────────────
url = data.movies.url

# ── Shared brush parameter (2-D rectangular selection) ───────────────────────
brush = alt.selection_interval(encodings=["x", "y"])

# ── Shared bin definitions ───────────────────────────────────────────────────
x_binned = alt.X("IMDB_Rating:Q").bin(maxbins=20)
y_binned = alt.Y("Rotten_Tomatoes_Rating:Q").bin(maxbins=20)

# ══════════════════════════════════════════════════════════════════════════════
# CENTER – 2-D binned heatmap
# ══════════════════════════════════════════════════════════════════════════════
heatmap = (
    alt.Chart(url)
    .mark_rect()
    .encode(
        x=x_binned,
        y=y_binned,
        color=alt.Color("count():Q", scale=alt.Scale(scheme="viridis")),
    )
    .add_params(brush)
    .properties(title="IMDB vs Rotten Tomatoes Ratings")
)

# ══════════════════════════════════════════════════════════════════════════════
# TOP – marginal histogram of IMDB_Rating
# ══════════════════════════════════════════════════════════════════════════════

# Baseline layer: all records (grey bars)
top_base = (
    alt.Chart(url)
    .mark_bar(color="lightgray")
    .encode(
        x=x_binned,
        y=alt.Y("count():Q", axis=alt.Axis(title="Count")),
    )
)

# Filtered layer: only records inside the brush
top_filtered = (
    alt.Chart(url)
    .mark_bar(color="steelblue")
    .encode(
        x=x_binned,
        y=alt.Y("count():Q"),
    )
    .transform_filter(brush)
)

top_hist = alt.layer(top_base, top_filtered).properties(title="IMDB Rating Distribution")

# ══════════════════════════════════════════════════════════════════════════════
# RIGHT – marginal histogram of Rotten_Tomatoes_Rating (horizontal bars)
# ══════════════════════════════════════════════════════════════════════════════

# Baseline layer: all records (grey bars)
right_base = (
    alt.Chart(url)
    .mark_bar(color="lightgray")
    .encode(
        x=alt.X("count():Q", axis=alt.Axis(title="Count")),
        y=y_binned,
    )
)

# Filtered layer: only records inside the brush
right_filtered = (
    alt.Chart(url)
    .mark_bar(color="steelblue")
    .encode(
        x=alt.X("count():Q"),
        y=y_binned,
    )
    .transform_filter(brush)
)

right_hist = alt.layer(right_base, right_filtered).properties(title="Rotten Tomatoes Rating Distribution")

# ══════════════════════════════════════════════════════════════════════════════
# COMPOUND – concatenate into the final dashboard
# ══════════════════════════════════════════════════════════════════════════════

# Top row: top histogram | empty placeholder
top_row = alt.hconcat(top_hist, alt.Chart().mark_text(text="").encode()).resolve_scale(
    x="independent", y="independent"
)

# Bottom row: heatmap | right histogram
bottom_row = alt.hconcat(heatmap, right_hist).resolve_scale(
    x="independent", y="independent"
)

chart = alt.vconcat(top_row, bottom_row).resolve_scale(
    x="independent", y="independent"
)

# ── Save ─────────────────────────────────────────────────────────────────────
chart.save("/home/user/myproject/chart.html")
print("✅ chart.html saved successfully.")
