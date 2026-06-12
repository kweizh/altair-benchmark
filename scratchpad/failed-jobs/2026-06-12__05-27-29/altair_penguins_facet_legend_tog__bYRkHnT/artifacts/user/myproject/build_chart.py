import altair as alt
import pandas as pd

# Load the penguins dataset from vega_datasets GitHub
# (The installed vega_datasets version doesn't include penguins,
#  so we fetch it directly from the canonical source.)
source = pd.read_json(
    "https://raw.githubusercontent.com/vega/vega-datasets/main/data/penguins.json"
)

# Create a point selection projected over Species, bound to the legend
# Clicking a legend entry toggles the corresponding species across all facets
species_select = alt.selection_point(
    fields=["Species"],
    bind="legend",
    name="species_sel",
)

# Build the base scatter chart
base = alt.Chart(source).mark_point().encode(
    x=alt.X("Beak Length (mm):Q").scale(zero=False),
    y=alt.Y("Body Mass (g):Q").scale(zero=False),
    color=alt.Color("Species:N"),
    opacity=alt.condition(
        species_select,
        alt.value(1),
        alt.value(0.1),
    ),
).add_params(
    species_select
)

# Facet by Island as columns, resolve y scale independently per panel
chart = base.facet(
    column="Island:N",
).resolve_scale(
    y="independent",
)

# Save artifacts
chart.save("/home/user/myproject/chart.html")
chart.save("/home/user/myproject/chart.json")
print("Done – chart.html and chart.json saved.")