"""Cross-filtering dashboard on the Cars dataset with Vega-Altair.

Layout: (A | B) & C, where:
  A — Scatter plot (Horsepower vs MPG, colored by Origin) with interval brush
  B — Horizontal bar chart (Origin vs count) filtered by brush
  C — Binned 2D heatmap (Weight vs Acceleration) filtered by brush
"""

import altair as alt
from vega_datasets import data


def main() -> None:
    source = data.cars()

    # Define the interval brush selection (x and y encodings).
    brush = alt.selection_interval(encodings=["x", "y"])

    # View A: Scatter plot of Horsepower vs Miles_per_Gallon, colored by Origin.
    view_a = (
        alt.Chart(source)
        .mark_point()
        .encode(
            x="Horsepower:Q",
            y="Miles_per_Gallon:Q",
            color="Origin:N",
        )
        .add_params(brush)
    )

    # View B: Horizontal bar chart — Origin vs count(), filtered by brush.
    view_b = (
        alt.Chart(source)
        .mark_bar()
        .encode(
            y="Origin:N",
            x="count():Q",
        )
        .transform_filter(brush)
    )

    # View C: Binned 2D heatmap — Weight_in_lbs vs Acceleration, filtered by brush.
    view_c = (
        alt.Chart(source)
        .mark_rect()
        .encode(
            x=alt.X("Weight_in_lbs:Q").bin(),
            y=alt.Y("Acceleration:Q").bin(),
            color="count():Q",
        )
        .transform_filter(brush)
    )

    # Compose layouts: (A | B) & C
    chart = (view_a | view_b) & view_c

    chart.save("/home/user/myproject/chart.html")


if __name__ == "__main__":
    main()
