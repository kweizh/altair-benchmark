"""Build the barley grouped-bar chart HTML.

Constructs a faceted, grouped bar chart from the ``data.barley`` dataset
and writes the result to ``/home/user/altair_task/output/chart.html``.
"""

import os

import altair as alt
from vega_datasets import data


def main() -> None:
    output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")
    os.makedirs(output_dir, exist_ok=True)

    barley = data.barley()

    # -- grouped bars: mean(yield) per (site, variety) -----------------------
    bars = (
        alt.Chart(barley)
        .mark_bar()
        .encode(
            x=alt.X(
                "site:N",
                axis=alt.Axis(title="Site"),
                sort=alt.Sort(field="yield", op="mean", order="descending"),
            ),
            y=alt.Y("mean(yield):Q", axis=alt.Axis(title="Mean Yield")),
            xOffset=alt.XOffset("variety:N"),
            color=alt.Color("variety:N", scale=alt.Scale(scheme="tableau10")),
        )
    )

    # -- per-site mean tick overlay ------------------------------------------
    ticks = (
        alt.Chart(barley)
        .transform_aggregate(mean_yield="mean(yield)", groupby=["site", "year"])
        .mark_tick(thickness=2, color="black")
        .encode(
            x=alt.X(
                "site:N",
                sort=alt.Sort(field="yield", op="mean", order="descending"),
            ),
            y=alt.Y("mean_yield:Q"),
        )
    )

    # -- layer bars + ticks, then facet by year ------------------------------
    layered = alt.layer(bars, ticks, data=barley).facet(
        column=alt.Column("year:O", header=alt.Header(title="Year")),
        title=alt.TitleParams(
            text="Barley Yield by Site and Variety",
            subtitle="Grouped bars with per-site mean overlay",
        ),
    )

    # -- resolve scale so bars and ticks share the same x-axis ---------------
    layered = layered.resolve_scale(x="independent")

    out_path = os.path.join(output_dir, "chart.html")
    layered.save(out_path)
    print(f"Chart saved to {out_path}")


if __name__ == "__main__":
    main()
