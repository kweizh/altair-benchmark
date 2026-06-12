#!/usr/bin/env python3
"""
Iris dataset: petalWidth vs petalLength with four layers:
  A — raw scatter points
  B — parametric regression line (solid)
  C — LOESS smoothed line (dashed)
  D — 95% confidence error band
"""

import altair as alt
from vega_datasets import data

# ── Load data ────────────────────────────────────────────────────────────────
iris = data.iris()

# ── Base chart ───────────────────────────────────────────────────────────────
base = alt.Chart(iris).encode(
    x=alt.X("petalLength:Q", title="Petal Length (cm)"),
    y=alt.Y("petalWidth:Q", title="Petal Width (cm)"),
    color=alt.Color("species:N", title="Species"),
)

# ── Layer A — Raw points ─────────────────────────────────────────────────────
points = base.mark_point(opacity=0.6, size=60)

# ── Layer B — Parametric regression line (solid) ─────────────────────────────
regression = base.mark_line().transform_regression(
    "petalLength", "petalWidth", groupby=["species"]
)

# ── Layer C — LOESS smoothed line (dashed) ───────────────────────────────────
loess = base.mark_line(strokeDash=[6, 4]).transform_loess(
    "petalLength", "petalWidth", groupby=["species"], bandwidth=0.6
)

# ── Layer D — 95% confidence error band ──────────────────────────────────────
errorband = base.mark_errorband(extent="ci").encode(
    y=alt.Y("petalWidth:Q", title="Petal Width (cm)"),
    x=alt.X("petalLength:Q", title="Petal Length (cm)"),
)

# ── Combine layers ───────────────────────────────────────────────────────────
chart = alt.layer(errorband, points, regression, loess, data=iris).properties(
    width=600,
    height=400,
    title=alt.Title(
        text="Iris Dataset: Petal Dimensions by Species",
        subtitle=[
            "Raw measurements with parametric regression, LOESS trend (bandwidth=0.6),",
            "and 95% confidence band — grouped by species",
        ],
    ),
)

# ── Save outputs ─────────────────────────────────────────────────────────────
chart.save("/home/user/iris_chart/chart.json")
chart.save("/home/user/iris_chart/chart.html")

# ── Log confirmation ─────────────────────────────────────────────────────────
log_path = "/home/user/iris_chart/output.log"
with open(log_path, "w") as f:
    f.write(f"Chart saved: /home/user/iris_chart/chart.html\n")
print(f"Chart saved: /home/user/iris_chart/chart.html")
