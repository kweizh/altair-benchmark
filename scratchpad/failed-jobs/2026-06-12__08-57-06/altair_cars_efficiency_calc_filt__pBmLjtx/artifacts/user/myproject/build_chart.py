import altair as alt
from vega_datasets import data

chart = (
    alt.Chart(data.cars.url)
    .transform_calculate(Efficiency="datum.Miles_per_Gallon / datum.Weight_in_lbs")
    .transform_filter(alt.datum.Efficiency > 0.01)
    .mark_bar()
    .encode(
        alt.X("Cylinders:O").sort("ascending"),
        alt.Y("mean(Efficiency):Q").axis(title="Mean Efficiency (mpg/lb)"),
        alt.Color("Cylinders:O").scale(scheme="category10"),
    )
)

chart.save("/home/user/myproject/chart.html")
print("chart.html saved successfully")
