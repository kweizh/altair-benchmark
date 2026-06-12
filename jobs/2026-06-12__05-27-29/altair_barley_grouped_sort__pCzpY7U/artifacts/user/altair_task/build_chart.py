#!/usr/bin/env python3
"""Build a faceted grouped bar chart from the barley dataset with per-site mean overlay."""

import altair as alt
from vega_datasets import data

# Load the barley dataset
barley = data.barley()

# --- Layer 1: Grouped bars (mean yield per site x variety) ---
bars = (
    alt.Chart(barley)
    .mark_bar()
    .encode(
        x=alt.X("site:N")
        .sort(field="yield", op="mean", order="descending")
        .title("Site"),
        y=alt.Y("mean(yield):Q").title("Mean Yield"),
        xOffset=alt.XOffset("variety:N"),
        color=alt.Color("variety:N").scale(scheme="tableau10"),
    )
)

# --- Layer 2: Per-site mean tick overlay ---
# Derive per-site mean inside the spec using transform_aggregate
ticks = (
    alt.Chart(barley)
    .mark_tick(thickness=2, color="black")
    .transform_aggregate(
        mean_yield="mean(yield)",
        groupby=["site", "year"],
    )
    .encode(
        x=alt.X("site:N")
        .sort(field="yield", op="mean", order="descending"),
        y=alt.Y("mean_yield:Q").title("Mean Yield"),
    )
)

# Combine layers and facet by year
chart = alt.layer(bars, ticks).facet(
    facet="year:O",
    title=alt.Title(
        text="Barley Yield by Site and Variety",
        subtitle="Grouped bars show mean yield per variety; ticks show per-site average across varieties",
    ),
)

# Save as standalone HTML
chart.save("/home/user/altair_task/output/chart.html")
print("Chart saved to /home/user/altair_task/output/chart.html")
