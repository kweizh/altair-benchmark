"""
Iris Regression + LOESS + Confidence Band
==========================================
Four-layer Altair chart of the classic Iris dataset:
  Layer A - raw scatter points, coloured by species
  Layer B - parametric regression line per species
  Layer C - LOESS smoothed dashed line per species
  Layer D - 95% confidence error-band per species
"""

import pathlib
import altair as alt
from vega_datasets import data as vega_data

# -- output paths
OUT_DIR = pathlib.Path("/home/user/iris_chart")
OUT_DIR.mkdir(parents=True, exist_ok=True)

JSON_PATH = OUT_DIR / "chart.json"
HTML_PATH = OUT_DIR / "chart.html"
LOG_PATH  = OUT_DIR / "output.log"

# -- data
iris = vega_data.iris()
source = alt.Chart(iris)

# -- shared encodings
x_enc     = alt.X("petalLength:Q", title="Petal Length (cm)")
y_enc     = alt.Y("petalWidth:Q",  title="Petal Width (cm)")
color_enc = alt.Color("species:N", title="Species")

# -- Layer A: raw scatter points
layer_points = (
    source.mark_point(filled=True, opacity=0.6)
    .encode(
        x=x_enc,
        y=y_enc,
        color=color_enc,
        tooltip=[
            alt.Tooltip("species:N",     title="Species"),
            alt.Tooltip("petalLength:Q", title="Petal Length", format=".2f"),
            alt.Tooltip("petalWidth:Q",  title="Petal Width",  format=".2f"),
        ],
    )
)

# -- Layer B: parametric regression line
layer_regression = (
    source.transform_regression(
        "petalLength",
        "petalWidth",
        groupby=["species"],
    )
    .mark_line(strokeWidth=2)
    .encode(
        x=x_enc,
        y=y_enc,
        color=color_enc,
    )
)

# -- Layer C: LOESS smoothed dashed line
layer_loess = (
    source.transform_loess(
        "petalLength",
        "petalWidth",
        groupby=["species"],
        bandwidth=0.6,
    )
    .mark_line(strokeWidth=2, strokeDash=[4, 4])
    .encode(
        x=x_enc,
        y=y_enc,
        color=color_enc,
    )
)

# -- Layer D: 95% confidence error-band
layer_band = (
    source.mark_errorband(extent="ci", opacity=0.15)
    .encode(
        x=x_enc,
        y=y_enc,
        color=color_enc,
    )
)

# -- Compose: band sits underneath points for correct visual stacking
title = alt.Title(
    text="Iris Dataset - Petal Dimensions by Species",
    subtitle=[
        "Solid line: parametric regression  |  Dashed line: LOESS (bandwidth = 0.6)",
        "Shaded region: 95% bootstrapped confidence band",
    ],
)

chart = (
    alt.layer(layer_band, layer_points, layer_regression, layer_loess)
    .properties(
        title=title,
        width=600,
        height=400,
    )
    .interactive()
)

# -- Persist artifacts
chart.save(str(JSON_PATH))
chart.save(str(HTML_PATH))

log_message = f"Chart saved: {HTML_PATH}"
LOG_PATH.write_text(log_message + "\n", encoding="utf-8")

print(log_message)
print(f"Chart saved: {JSON_PATH}")
