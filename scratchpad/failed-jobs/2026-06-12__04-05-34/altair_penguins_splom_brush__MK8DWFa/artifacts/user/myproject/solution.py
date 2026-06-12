"""Solution for the Penguins SPLOM brush task.

This script builds a Scatter PLOt Matrix (SPLOM) of the Palmer Penguins dataset
with a single, globally-resolved interval brush using Vega-Altair, and saves the
chart to `/home/user/myproject/chart.html`.
"""

import altair as alt

try:
    from altair.datasets import data
except ImportError:
    from vega_datasets import data

OUTPUT_HTML = "/home/user/myproject/chart.html"


def main() -> None:
    # Resolve the penguins dataset URL
    if hasattr(data, "penguins"):
        penguins_url = data.penguins.url
    else:
        # Fallback to the known jsDelivr CDN URL for vega-datasets penguins
        penguins_url = "https://cdn.jsdelivr.net/npm/vega-datasets@v3.2.1/data/penguins.json"

    # Define the 4 quantitative features to repeat over
    features = [
        "Beak Length (mm)",
        "Beak Depth (mm)",
        "Flipper Length (mm)",
        "Body Mass (g)",
    ]

    # Create a single interval selection brush projected over x and y encodings
    brush = alt.selection_interval(
        name="brush",
        encodings=["x", "y"]
    )

    # Build the base scatter plot cell
    cell = alt.Chart(penguins_url).mark_point().encode(
        x=alt.X(
            alt.repeat("column"),
            type="quantitative",
            scale=alt.Scale(zero=False)
        ),
        y=alt.Y(
            alt.repeat("row"),
            type="quantitative",
            scale=alt.Scale(zero=False)
        ),
        color=alt.condition(brush, "Species:N", alt.value("lightgray"))
    ).add_params(
        brush
    )

    # Repeat the cell across rows and columns to form the SPLOM
    chart = cell.repeat(
        row=features,
        column=features
    )

    # Save the resulting chart to a self-contained HTML file
    chart.save(OUTPUT_HTML)
    print(f"Successfully generated SPLOM chart at: {OUTPUT_HTML}")


if __name__ == "__main__":
    main()
