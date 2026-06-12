import altair as alt
from vega_datasets import data

# Data source
source = data.movies.url

# Interval selection: 2D brush on the heatmap
brush = alt.selection_interval(encodings=['x', 'y'])

# ── Center: 2D binned heatmap ──────────────────────────────────────
heatmap = (
    alt.Chart(source)
    .mark_rect()
    .encode(
        x=alt.X('IMDB_Rating:Q', bin=alt.Bin(maxbins=20)),
        y=alt.Y('Rotten_Tomatoes_Rating:Q', bin=alt.Bin(maxbins=20)),
        color=alt.Color('count()', scale=alt.Scale(scheme='viridis')),
    )
    .add_params(brush)
)

# ── Top: marginal histogram of IMDB_Rating ─────────────────────────
imdb_bin = alt.Bin(maxbins=20)

# Baseline (all data) – gray bars
top_base = (
    alt.Chart(source)
    .mark_bar(color='lightgray')
    .encode(
        x=alt.X('IMDB_Rating:Q', bin=imdb_bin),
        y=alt.Y('count()'),
    )
)

# Filtered (brushed data) – colored bars
top_filter = (
    alt.Chart(source)
    .mark_bar(color='steelblue')
    .encode(
        x=alt.X('IMDB_Rating:Q', bin=imdb_bin),
        y=alt.Y('count()'),
    )
    .transform_filter(brush)
)

top_marginal = alt.layer(top_base, top_filter)

# ── Right: marginal histogram of Rotten_Tomatoes_Rating ────────────
rt_bin = alt.Bin(maxbins=20)

# Baseline (all data) – gray bars
right_base = (
    alt.Chart(source)
    .mark_bar(color='lightgray')
    .encode(
        x=alt.X('count()'),
        y=alt.Y('Rotten_Tomatoes_Rating:Q', bin=rt_bin),
    )
)

# Filtered (brushed data) – colored bars
right_filter = (
    alt.Chart(source)
    .mark_bar(color='steelblue')
    .encode(
        x=alt.X('count()'),
        y=alt.Y('Rotten_Tomatoes_Rating:Q', bin=rt_bin),
    )
    .transform_filter(brush)
)

right_marginal = alt.layer(right_base, right_filter)

# ── Compose the compound chart ──────────────────────────────────────
# Top marginal on top of heatmap (vertical concat),
# then horizontal concat with right marginal.
chart = (top_marginal & heatmap) | right_marginal

# Save to HTML
chart.save('/home/user/myproject/chart.html')
print("Chart saved to /home/user/myproject/chart.html")