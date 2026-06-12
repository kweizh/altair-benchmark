import altair as alt

# Use the iris dataset from vega_datasets (URL-based source)
url = "https://vega.github.io/vega-datasets/data/iris.json"

# Define the bound selection parameter with a dropdown widget
species_param = alt.param(
    name="species_selector",
    bind=alt.binding_select(
        options=["setosa", "versicolor", "virginica"],
        name="Species: ",
    ),
    value="setosa",
)

# Build the scatter plot
chart = (
    alt.Chart(url)
    .mark_circle(size=80)
    .encode(
        x=alt.X("sepalLength:Q", title="Sepal Length"),
        y=alt.Y("sepalWidth:Q", title="Sepal Width"),
        color=alt.when("datum.species == species_selector")
        .then(alt.Color("species:N", legend=alt.Legend(title="Species")))
        .otherwise(alt.value("lightgray")),
    )
    .add_params(species_param)
)

# Save as self-contained HTML
chart.save("/home/user/myproject/chart.html")
print("chart.html generated successfully.")
