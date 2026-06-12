"""Build a layered Altair chart of Iowa electricity net generation.

The chart contains four layers:
1. IQR error band of net_generation per year (across source groups)
2. Median net_generation line per year
3. Horizontal dashed red rule at y=0
4. Text annotation for the year with the largest median net_generation
"""

import altair as alt
from vega_datasets import data


def build_chart() -> None:
    # ------------------------------------------------------------------
    # Data
    # ------------------------------------------------------------------
    source = data.iowa_electricity.url

    # ------------------------------------------------------------------
    # Shared temporal x encoding
    # ------------------------------------------------------------------
    x_enc = alt.X(
        "year(year):T",
        title="Year",
        scale=alt.Scale(type="time"),
    )

    # ------------------------------------------------------------------
    # Layer 1 – IQR error band (monotone interpolation)
    # ------------------------------------------------------------------
    errorband = (
        alt.Chart(source)
        .mark_errorband(extent="iqr", interpolate="monotone")
        .encode(
            x=x_enc,
            y=alt.Y("net_generation:Q", title="Net Generation"),
        )
    )

    # ------------------------------------------------------------------
    # Layer 2 – Median line
    # ------------------------------------------------------------------
    median_line = (
        alt.Chart(source)
        .mark_line()
        .encode(
            x=x_enc,
            y=alt.Y("median(net_generation):Q"),
        )
    )

    # ------------------------------------------------------------------
    # Layer 3 – Horizontal dashed red rule at y = 0
    # ------------------------------------------------------------------
    zero_rule = (
        alt.Chart(alt.Data(values=[{"y": 0}]))
        .mark_rule(strokeDash=[4, 4], color="red")
        .encode(y=alt.Y("y:Q"))
    )

    # ------------------------------------------------------------------
    # Layer 4 – Text annotation for the max-median year
    # ------------------------------------------------------------------
    # Precompute per-year median, rank by descending median, keep top.
    annotation = (
        alt.Chart(source)
        .mark_text(
            align="left",
            dx=5,
            dy=-10,
            fontSize=12,
            fontWeight="bold",
        )
        .encode(
            x=x_enc,
            y=alt.Y("median_net_generation:Q"),
            text=alt.Text("label:N"),
        )
        .transform_aggregate(
            median_net_generation="median(net_generation)",
            groupby=["year"],
        )
        .transform_window(
            rank="rank()",
            sort=[alt.SortField("median_net_generation", order="descending")],
        )
        .transform_filter(alt.datum.rank == 1)
        .transform_calculate(
            label="'Year: ' + toString(year(year)) + ', Median: ' + toString(round(median_net_generation * 100) / 100)",
        )
    )

    # ------------------------------------------------------------------
    # Combine layers
    # ------------------------------------------------------------------
    chart = alt.layer(
        errorband,
        median_line,
        zero_rule,
        annotation,
    ).properties(
        title=alt.TitleParams(
            text="Iowa Electricity Net Generation Distribution by Year",
            subtitle="IQR error band with median line; red rule at y=0; annotation marks the year with the largest median output",
        ),
    )

    # ------------------------------------------------------------------
    # Save
    # ------------------------------------------------------------------
    output_path = "/home/user/myproject/chart.html"
    chart.save(output_path)
    print(f"Chart written: {output_path}")


if __name__ == "__main__":
    build_chart()
