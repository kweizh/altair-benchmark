import altair as alt
from vega_datasets import data

# URL-based data source (no local DataFrame)
iris_url = data.iris.url

# Bound dropdown widget
dropdown = alt.binding_select(
    options=["setosa", "versicolor", "virginica"],
    name="Species: ",
)

# Parameter that holds the currently selected species
species_param = alt.param(
    value="setosa",       # sensible default so the chart looks right on load
    bind=dropdown,
)

# Conditional color: matching species keeps its nominal color, others go gray
color_encoding = (
    alt.when(f"datum.species == {species_param.name}")
    .then(alt.Color("species:N"))
    .otherwise(alt.value("lightgray"))
)

chart = (
    alt.Chart(iris_url)
    .mark_point()
    .encode(
        x=alt.X("sepalLength:Q"),
        y=alt.Y("sepalWidth:Q"),
        color=color_encoding,
    )
    .add_params(species_param)
)

chart.save("/home/user/myproject/chart.html")
print("Saved chart.html")
