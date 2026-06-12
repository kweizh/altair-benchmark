#!/usr/bin/env python3
"""
Iris Regression + LOESS + Confidence Band visualization using Altair.

Produces:
  - chart.json  (Vega-Lite spec)
  - chart.html  (standalone interactive HTML)
  - output.log   (log confirming saves)
"""

import os
import altair as alt
from vega_datasets import data

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
HTML_PATH = os.path.join(SCRIPT_DIR, "chart.html")
JSON_PATH = os.path.join(SCRIPT_DIR, "chart.json")
LOG_PATH = os.path.join(SCRIPT_DIR, "output.log")

# Load Iris dataset
iris = data.iris()

# Base chart with shared encodings
base = alt.Chart(iris).encode(
    x=alt.X("petalLength:Q", title="Petal Length (cm)"),
    y=alt.Y("petalWidth:Q", title="Petal Width (cm)"),
    color=alt.Color("species:N", title="Species"),
)

# Layer A — Raw scatter points
points = base.mark_point(filled=True, size=50)

# Layer B — Parametric regression line per species
regression = base.transform_regression(
    "petalLength", "petalWidth", groupby=["species"]
).mark_line()

# Layer C — LOESS smoothed line per species (dashed)
loess = base.transform_loess(
    "petalLength", "petalWidth", groupby=["species"], bandwidth=0.6
).mark_line(strokeDash=[4, 4])

# Layer D — 95% confidence band per species
confidence = base.mark_errorband(extent="ci")

# Compose layered chart — band underneath, then lines, then points on top
chart = alt.layer(
    confidence,
    regression,
    loess,
    points,
).properties(
    width=600,
    height=400,
    title=alt.Title(
        text="Iris Petal Dimensions: Regression & LOESS",
        subtitle=[
            "Solid lines = parametric regression; dashed lines = LOESS (bandwidth=0.6)",
            "Shaded regions = 95% confidence intervals around the mean",
        ],
    ),
)

# Save artefacts
chart.save(JSON_PATH)
chart.save(HTML_PATH)

# Write log
with open(LOG_PATH, "w") as f:
    f.write(f"Chart saved: {HTML_PATH}\n")

print(f"Chart saved: {HTML_PATH}")
print(f"Spec saved:  {JSON_PATH}")
print(f"Log saved:   {LOG_PATH}")