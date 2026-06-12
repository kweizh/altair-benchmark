import json
import altair as alt
from palmerpenguins import load_penguins

# Load the penguins dataset and rename columns to match the vega_datasets schema
_raw = load_penguins()
penguins = _raw.rename(
    columns={
        "species": "Species",
        "island": "Island",
        "bill_length_mm": "Beak Length (mm)",
        "bill_depth_mm": "Beak Depth (mm)",
        "flipper_length_mm": "Flipper Length (mm)",
        "body_mass_g": "Body Mass (g)",
        "sex": "Sex",
    }
).dropna(subset=["Beak Length (mm)", "Body Mass (g)"])

# Define a point selection projected over 'Species', bound to the legend
species_selection = alt.selection_point(
    fields=["Species"],
    bind="legend",
)

# Base scatter chart
base = (
    alt.Chart(penguins)
    .mark_point()
    .encode(
        x=alt.X("Beak Length (mm):Q").scale(zero=False),
        y=alt.Y("Body Mass (g):Q").scale(zero=False),
        color=alt.Color("Species:N"),
        opacity=alt.condition(
            species_selection,
            alt.value(1.0),   # selected  → fully opaque
            alt.value(0.1),   # otherwise → dimmed
        ),
        tooltip=["Species:N", "Island:N", "Beak Length (mm):Q", "Body Mass (g):Q"],
    )
    .add_params(species_selection)
)

# Facet by Island (columns), with independent y scales
chart = (
    base.facet(
        column=alt.Column("Island:N"),
    )
    .resolve_scale(y="independent")
)

# Save artifacts
chart.save("/home/user/myproject/chart.html")

spec = chart.to_dict()
with open("/home/user/myproject/chart.json", "w") as f:
    json.dump(spec, f, indent=2)

print("Saved chart.html and chart.json")
print("Spec keys:", list(spec.keys()))
