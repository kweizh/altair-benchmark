import altair as alt
import json
import seaborn as sns

# Load penguins dataset from seaborn (same Palmer penguins data)
penguins = sns.load_dataset("penguins")

# Rename columns to match the expected Vega-Lite field names
penguins = penguins.rename(columns={
    "species": "Species",
    "island": "Island",
    "bill_length_mm": "Beak Length (mm)",
    "body_mass_g": "Body Mass (g)",
})

# Define the point selection bound to the Species legend
species_selection = alt.selection_point(
    fields=["Species"],
    bind="legend",
    name="species_legend"
)

# Build the base scatter chart
base = alt.Chart(penguins).mark_point().encode(
    x=alt.X("Beak Length (mm):Q", scale=alt.Scale(zero=False)),
    y=alt.Y("Body Mass (g):Q", scale=alt.Scale(zero=False)),
    color=alt.Color("Species:N"),
    opacity=alt.condition(
        species_selection,
        alt.value(1.0),      # fully opaque when selected
        alt.value(0.1)       # dimmed when not selected
    )
).add_params(
    species_selection
)

# Facet by Island as columns, with independent y scales
chart = base.facet(
    column=alt.Column("Island:N"),
    resolve=alt.Resolve(scale={"y": "independent"})
)

# Save the HTML
chart.save("/home/user/myproject/chart.html")

# Save the Vega-Lite JSON spec
spec = chart.to_dict()
with open("/home/user/myproject/chart.json", "w") as f:
    json.dump(spec, f, indent=2)

print("chart.html and chart.json written successfully.")
