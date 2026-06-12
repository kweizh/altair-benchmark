"""
Barley Yield: Grouped Bar Chart with Sorted Sites and Mean Overlay

Builds a faceted, grouped bar chart from the classic barley dataset using
Vega-Altair.  Writes a self-contained HTML file to
``/home/user/altair_task/output/chart.html``.
"""

import os
import pathlib

import altair as alt
from altair.datasets import data as vega_data


def main() -> None:
    # ------------------------------------------------------------------
    # 1. Load the dataset
    # ------------------------------------------------------------------
    barley = vega_data.barley()

    # ------------------------------------------------------------------
    # 2. Grouped bar chart layer
    #    - x  : site, sorted descending by mean(yield)
    #    - y  : mean(yield)
    #    - xOffset: variety  ->  grouped (not stacked) bars
    #    - color: variety, tableau10 scheme
    # ------------------------------------------------------------------
    bars = (
        alt.Chart()
        .mark_bar()
        .encode(
            x=alt.X(
                "site:N",
                sort=alt.EncodingSortField(
                    field="yield", op="mean", order="descending"
                ),
                title="Site",
                axis=alt.Axis(labelAngle=-35),
            ),
            y=alt.Y(
                "mean(yield):Q",
                title="Mean Yield (bushels/acre)",
            ),
            xOffset=alt.XOffset("variety:N"),
            color=alt.Color(
                "variety:N",
                scale=alt.Scale(scheme="tableau10"),
                legend=alt.Legend(title="Variety", orient="right"),
            ),
            tooltip=[
                alt.Tooltip("site:N", title="Site"),
                alt.Tooltip("variety:N", title="Variety"),
                alt.Tooltip("mean(yield):Q", title="Mean Yield", format=".2f"),
            ],
        )
    )

    # ------------------------------------------------------------------
    # 3. Per-site mean-yield overlay (tick mark)
    #    Aggregate mean(yield) grouped by site + year *inside* the spec
    #    using transform_aggregate (no pre-aggregation in pandas).
    # ------------------------------------------------------------------
    mean_tick = (
        alt.Chart()
        .transform_aggregate(
            mean_yield="mean(yield)",
            groupby=["site", "year"],
        )
        .mark_tick(
            color="black",
            thickness=2,
            size=20,
            opacity=0.85,
        )
        .encode(
            x=alt.X(
                "site:N",
                sort=alt.EncodingSortField(
                    field="yield", op="mean", order="descending"
                ),
            ),
            y=alt.Y("mean_yield:Q"),
            tooltip=[
                alt.Tooltip("site:N", title="Site"),
                alt.Tooltip("mean_yield:Q", title="Site Mean Yield", format=".2f"),
            ],
        )
    )

    # ------------------------------------------------------------------
    # 4. Layer -> facet by year
    # ------------------------------------------------------------------
    chart = (
        alt.layer(bars, mean_tick, data=barley)
        .facet(
            facet=alt.Facet("year:O", title="Year"),
            columns=1,
        )
        .properties(
            title=alt.TitleParams(
                text="Barley Yield by Variety and Site",
                subtitle=(
                    "Grouped bars show mean yield per variety; "
                    "black tick marks indicate per-site mean across all varieties."
                ),
                fontSize=18,
                subtitleFontSize=13,
                anchor="middle",
            )
        )
        .configure_view(stroke=None)
        .configure_axis(grid=True, gridOpacity=0.3)
    )

    # ------------------------------------------------------------------
    # 5. Save as a self-contained HTML file
    # ------------------------------------------------------------------
    output_path = pathlib.Path(
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "output", "chart.html")
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    chart.save(str(output_path))
    print(f"Chart saved -> {output_path.resolve()}")


if __name__ == "__main__":
    main()
