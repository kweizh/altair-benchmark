"""US County Unemployment Choropleth with Linked Brushable Histogram.

Builds an interactive dashboard that combines:
1. A US county choropleth map (Albers USA projection, threshold color scale).
2. A histogram of unemployment rates with an interval brush that filters the map.
"""

import altair as alt
from vega_datasets import data


def main() -> None:
    # ── shared interval brush parameter ──────────────────────────────────
    brush = alt.selection_interval(encodings=["x"], name="brush")

    # ── choropleth map ───────────────────────────────────────────────────
    counties = alt.topo_feature(data.us_10m.url, "counties")

    map_chart = (
        alt.Chart(counties)
        .mark_geoshape()
        .transform_lookup(
            lookup="id",
            from_=alt.LookupData(
                data=data.unemployment.url, key="id", fields=["rate"]
            ),
        )
        .encode(
            color=alt.Color(
                "rate:Q",
                scale=alt.Scale(
                    domain=[0.05, 0.10, 0.15, 0.20],
                    type="threshold",
                    scheme="blues",
                ),
                title="Unemployment Rate",
            ),
            tooltip=["id:N", "rate:Q"],
        )
        .project(type="albersUsa")
        .transform_filter(brush)
    )

    # ── brushable histogram ──────────────────────────────────────────────
    hist = (
        alt.Chart(data.unemployment.url)
        .mark_bar()
        .encode(
            alt.X("rate:Q", bin=True, title="Unemployment Rate"),
            alt.Y("count()", title="Number of Counties"),
        )
        .add_params(brush)
    )

    # ── combine and save ─────────────────────────────────────────────────
    dashboard = alt.vconcat(map_chart, hist).resolve_scale(color="independent")

    dashboard.save("chart.html")
    print("Dashboard saved to chart.html")


if __name__ == "__main__":
    main()
