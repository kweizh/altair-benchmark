"""Penguins SPLOM with linked brushing using Vega-Altair."""

import altair as alt

OUTPUT_HTML = "/home/user/myproject/chart.html"

# The four quantitative features for the SPLOM
features = [
    'Beak Length (mm)',
    'Beak Depth (mm)',
    'Flipper Length (mm)',
    'Body Mass (g)',
]

# Data source — vega-datasets v2 penguins JSON (matches the column names above)
penguins_url = 'https://cdn.jsdelivr.net/npm/vega-datasets@v2/data/penguins.json'

# Single global interval brush projected on both x and y
brush = alt.selection_interval(encodings=['x', 'y'])

# Base chart: each cell of the SPLOM
base = (
    alt.Chart(penguins_url)
    .mark_point()
    .encode(
        x=alt.X(alt.repeat('column'), type='quantitative', scale=alt.Scale(zero=False)),
        y=alt.Y(alt.repeat('row'), type='quantitative', scale=alt.Scale(zero=False)),
        color=alt.condition(brush, alt.Color('Species:N'), alt.value('lightgray')),
    )
    .add_params(brush)
)

# Build the 4×4 SPLOM
chart = base.repeat(row=features, column=features)

# Save as self-contained HTML
chart.save(OUTPUT_HTML)


def main() -> None:
    pass  # Chart is saved at module level for simplicity


if __name__ == "__main__":
    main()