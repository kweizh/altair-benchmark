"""
Vega-Altair interactive dashboard on the cars dataset with shared legend selection.

Layout: (A | B) & C
  A - Scatter: Horsepower vs Miles_per_Gallon, colored by Origin
  B - Stacked bar: Cylinders (ordinal) vs count(), colored by Origin
  C - Histogram: Acceleration (binned) vs count(), colored by Origin

A single shared `selection_point` on Origin, bound to the legend, drives
opacity across all three views.
"""

import altair as alt
from vega_datasets import data

# ── Data ──────────────────────────────────────────────────────────────────────
source = data.cars()

# ── Shared legend selection ───────────────────────────────────────────────────
legend_selection = alt.selection_point(
    fields=["Origin"],
    bind="legend",
    name="legend_select",
)

# ── View A: Scatter ───────────────────────────────────────────────────────────
scatter = (
    alt.Chart(source)
    .mark_circle()
    .encode(
        x="Horsepower:Q",
        y="Miles_per_Gallon:Q",
        color="Origin:N",
        opacity=alt.condition(
            legend_selection,
            alt.value(1),
            alt.value(0.15),
        ),
    )
)

# ── View B: Stacked bar ───────────────────────────────────────────────────────
stacked_bar = (
    alt.Chart(source)
    .mark_bar()
    .encode(
        x="Cylinders:O",
        y="count():Q",
        color="Origin:N",
        opacity=alt.condition(
            legend_selection,
            alt.value(1),
            alt.value(0.15),
        ),
    )
)

# ── View C: Histogram ─────────────────────────────────────────────────────────
histogram = (
    alt.Chart(source)
    .mark_bar()
    .encode(
        x=alt.X("Acceleration:Q").bin(),
        y="count():Q",
        color="Origin:N",
        opacity=alt.condition(
            legend_selection,
            alt.value(1),
            alt.value(0.15),
        ),
    )
)

# ── Compose & save ────────────────────────────────────────────────────────────
chart = (scatter | stacked_bar) & histogram
chart = chart.add_params(legend_selection)

chart.save("/home/user/myproject/chart.html")
