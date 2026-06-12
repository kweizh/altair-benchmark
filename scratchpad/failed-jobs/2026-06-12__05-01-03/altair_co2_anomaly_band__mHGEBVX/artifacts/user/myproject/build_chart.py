"""
Iowa Electricity Anomaly Band Chart
Layered Vega-Altair visualization: IQR error band, median line,
zero rule, and a data-driven text annotation for the peak year.
"""

import altair as alt
from vega_datasets import data
import logging
import os

# ---------------------------------------------------------------------------
# Logging setup
# ---------------------------------------------------------------------------
LOG_PATH = "/home/user/myproject/output.log"
CHART_PATH = "/home/user/myproject/chart.html"

os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)

logging.basicConfig(
    filename=LOG_PATH,
    filemode="w",
    level=logging.INFO,
    format="%(message)s",
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Data source
# ---------------------------------------------------------------------------
iowa_url = data.iowa_electricity.url
source = alt.UrlData(url=iowa_url, format=alt.DataFormat(type="csv"))

# Shared x-axis encoding (temporal, year time-unit, time scale)
x_shared = alt.X(
    "year:T",
    timeUnit="year",
    title="Year",
    scale=alt.Scale(type="time"),
)

# ---------------------------------------------------------------------------
# Layer 1 — IQR error band (monotone interpolation)
# ---------------------------------------------------------------------------
layer_band = (
    alt.Chart(source)
    .mark_errorband(extent="iqr", interpolate="monotone")
    .encode(
        x=x_shared,
        y=alt.Y("net_generation:Q", title="Net Generation (MWh)"),
    )
)

# ---------------------------------------------------------------------------
# Layer 2 — Median line
# ---------------------------------------------------------------------------
layer_line = (
    alt.Chart(source)
    .mark_line(color="steelblue", strokeWidth=2)
    .encode(
        x=x_shared,
        y=alt.Y("median(net_generation):Q"),
    )
)

# ---------------------------------------------------------------------------
# Layer 3 — Horizontal dashed rule at y = 0, red
# ---------------------------------------------------------------------------
layer_rule = (
    alt.Chart()
    .mark_rule(color="red", strokeDash=[4, 4], strokeWidth=1.5)
    .encode(
        y=alt.YDatum(0)
    )
)

# ---------------------------------------------------------------------------
# Layer 4 — Text annotation: year with the largest median net_generation
#   Steps:
#     1. transform_aggregate  → median per year
#     2. transform_window     → rank by descending median
#     3. transform_filter     → keep only rank == 1
#     4. mark_text            → show "YYYY: value MWh"
# ---------------------------------------------------------------------------
layer_text = (
    alt.Chart(source)
    .transform_aggregate(
        median_gen="median(net_generation)",
        groupby=["year"],
    )
    .transform_window(
        rank="rank()",
        sort=[alt.SortField("median_gen", order="descending")],
    )
    .transform_filter("datum.rank === 1")
    .mark_text(
        align="left",
        dx=6,
        dy=-10,
        fontWeight="bold",
        fontSize=12,
        color="darkblue",
    )
    .encode(
        x=alt.X(
            "year:T",
            timeUnit="year",
            scale=alt.Scale(type="time"),
        ),
        y=alt.Y("median_gen:Q"),
        text=alt.Text("median_gen:Q", format=".0f"),
    )
)

# ---------------------------------------------------------------------------
# Compose chart
# ---------------------------------------------------------------------------
chart = (
    alt.layer(layer_band, layer_line, layer_rule, layer_text)
    .properties(
        width=720,
        height=400,
        title=alt.TitleParams(
            text="Iowa Electricity Net Generation by Year",
            subtitle="IQR band across source categories · median line · peak year annotated",
            anchor="start",
            fontSize=18,
            subtitleFontSize=13,
            subtitleColor="gray",
        ),
    )
)

# ---------------------------------------------------------------------------
# Save & log
# ---------------------------------------------------------------------------
chart.save(CHART_PATH)
logger.info("Chart written: %s", CHART_PATH)
print(f"Chart written: {CHART_PATH}")
