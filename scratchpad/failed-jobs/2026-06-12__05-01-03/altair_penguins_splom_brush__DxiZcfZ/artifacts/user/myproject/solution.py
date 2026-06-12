import altair as alt

# ---------------------------------------------------------------------------
# Data source
# ---------------------------------------------------------------------------
penguins_url = "https://cdn.jsdelivr.net/npm/vega-datasets@2/data/penguins.json"

# Quantitative features to include in the SPLOM
features = [
    "Beak Length (mm)",
    "Beak Depth (mm)",
    "Flipper Length (mm)",
    "Body Mass (g)",
]

# ---------------------------------------------------------------------------
# Single global interval brush projected onto both x and y encodings
# ---------------------------------------------------------------------------
brush = alt.selection_interval(
    encodings=["x", "y"],
    resolve="global",          # one shared brush across all repeat cells
)

# ---------------------------------------------------------------------------
# Base chart: one cell of the SPLOM
# ---------------------------------------------------------------------------
base = (
    alt.Chart(penguins_url)
    .mark_point(filled=True, opacity=0.7, size=40)
    .encode(
        x=alt.X(
            alt.repeat("column"),
            type="quantitative",
            scale=alt.Scale(zero=False),
        ),
        y=alt.Y(
            alt.repeat("row"),
            type="quantitative",
            scale=alt.Scale(zero=False),
        ),
        color=alt.condition(
            brush,
            alt.Color("Species:N"),   # inside brush -> color by species
            alt.value("lightgray"),   # outside brush -> gray
        ),
        tooltip=[
            alt.Tooltip("Species:N"),
            alt.Tooltip(alt.repeat("column"), type="quantitative"),
            alt.Tooltip(alt.repeat("row"), type="quantitative"),
        ],
    )
    .add_params(brush)
)

# ---------------------------------------------------------------------------
# Assemble the SPLOM with repeat
# ---------------------------------------------------------------------------
chart = (
    base.repeat(
        row=features,
        column=features,
    )
    .properties(
        title="Palmer Penguins SPLOM with Linked Brushing",
    )
    .configure_view(stroke=None)
)

# ---------------------------------------------------------------------------
# Save to self-contained HTML
# ---------------------------------------------------------------------------
output_path = "/home/user/myproject/chart.html"
chart.save(output_path)
print(f"Chart saved to {output_path}")
