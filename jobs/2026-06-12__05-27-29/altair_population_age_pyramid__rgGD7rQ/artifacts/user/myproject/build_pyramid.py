import altair as alt
import json
import os

# Ensure output directory exists
os.makedirs('/home/user/myproject', exist_ok=True)

# Data source URL (must match the acceptance criteria URL exactly)
population_url = "https://vega.github.io/vega-datasets/data/population.json"

# Distinct year values in the dataset
years = [1850, 1860, 1870, 1880, 1890, 1900, 1910, 1920, 1930, 1940, 1950, 1960, 1970, 1980, 1990, 2000]

# Year dropdown parameter bound to a binding_select
year_param = alt.param(
    value=1980,
    bind=alt.binding_select(options=years, name="Year: ")
)

# Build the back-to-back age pyramid chart
chart = (
    alt.Chart(population_url)
    .mark_bar()
    .encode(
        x=alt.X(
            "people_signed:Q",
            axis=alt.Axis(
                format=",",
                labelExpr="abs(datum.value)",
                title="Population",
            ),
        ),
        y=alt.Y(
            "age:O",
            sort="descending",
            title="Age",
        ),
        color=alt.Color(
            "sex:N",
            scale=alt.Scale(
                domain=[1, 2],
                range=["steelblue", "salmon"],
            ),
            legend=alt.Legend(
                labelExpr="datum.value == 1 ? 'Male' : 'Female'",
                title="Sex",
            ),
        ),
    )
    .transform_calculate(
        people_signed="datum.sex == 1 ? -datum.people : datum.people",
    )
    .transform_filter(
        alt.datum.year == year_param,
    )
    .add_params(year_param)
)

# Save the chart as a self-contained HTML file
chart.save("/home/user/myproject/pyramid.html")

# Save the Vega-Lite spec as JSON
spec = chart.to_dict()
with open("/home/user/myproject/pyramid_spec.json", "w") as f:
    json.dump(spec, f, indent=2)

print("Done! Files saved:")
print("  - /home/user/myproject/pyramid.html")
print("  - /home/user/myproject/pyramid_spec.json")
