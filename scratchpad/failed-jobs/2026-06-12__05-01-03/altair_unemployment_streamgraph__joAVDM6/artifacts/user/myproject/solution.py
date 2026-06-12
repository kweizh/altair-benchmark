"""
Altair Unemployment Streamgraph with Hover Ruler and Top-Series Annotation
--------------------------------------------------------------------------
Generates a self-contained HTML file at out/chart.html.
"""

import altair as alt
from vega_datasets import data

# ── 0. Disable the default 5 000-row guard ────────────────────────────────────
alt.data_transformers.disable_max_rows()

# ── 1. Data source (remote URL embedded in the spec) ─────────────────────────
source = data.unemployment_across_industries.url   # CDN URL → no local file needed

# ── 2. Hover selection – nearest-x, fires on pointerover ─────────────────────
hover = alt.selection_point(
    name="hover",
    on="pointerover",
    nearest=True,
    encodings=["x"],
    empty=False,
)

# ── 3. Base streamgraph (area layer) ─────────────────────────────────────────
area = (
    alt.Chart(source)
    .mark_area(interpolate="monotone")
    .encode(
        x=alt.X(
            "yearmonth(date):T",
            axis=alt.Axis(domain=False, format="%Y", tickSize=0),
            title=None,
        ),
        y=alt.Y(
            "sum(count):Q",
            stack="center",
            axis=None,          # hide Y axis – baseline is data-dependent
            title=None,
        ),
        color=alt.Color(
            "series:N",
            scale=alt.Scale(scheme="category20b"),
            legend=alt.Legend(orient="bottom", columns=5),
        ),
    )
    .add_params(hover)          # attach the selection to this layer
)

# ── 4. Vertical rule – appears only at the hovered month ─────────────────────
rule = (
    alt.Chart(source)
    .mark_rule(color="white", strokeWidth=2)
    .encode(
        x="yearmonth(date):T",
        opacity=alt.condition(hover, alt.value(0.85), alt.value(0)),
    )
)

# ── 5. Top-series annotation – window-rank per date, keep rank == 1 ──────────
#
#   transform_window:
#     - rank the rows within each date group by count descending
#     - "date_rank" = rank per (date) sorted by count DESC
#   transform_filter:
#     - keep only rank-1 row (the series with the highest count that month)
#   The text is shown only while the hover is active.
#
annotation = (
    alt.Chart(source)
    .mark_text(
        color="white",
        fontWeight="bold",
        fontSize=12,
        dy=-8,              # nudge slightly above the streamgraph centre
        align="center",
    )
    .encode(
        x="yearmonth(date):T",
        text=alt.condition(hover, "series:N", alt.value("")),
        opacity=alt.condition(hover, alt.value(1), alt.value(0)),
    )
    .transform_window(
        date_rank="rank()",
        sort=[alt.SortField("count", order="descending")],
        groupby=["date"],
    )
    .transform_filter("datum.date_rank === 1")
)

# ── 6. Compose layers ─────────────────────────────────────────────────────────
chart = (
    alt.layer(area, rule, annotation)
    .properties(
        title=alt.TitleParams(
            "US Unemployment Across Industries",
            fontSize=16,
            anchor="start",
        ),
        width=900,
        height=450,
    )
    .configure_view(strokeWidth=0)
)

# ── 7. Save self-contained HTML ───────────────────────────────────────────────
out_path = "out/chart.html"
chart.save(out_path, embed_options={"renderer": "svg"})
print(f"Chart saved → {out_path}")
