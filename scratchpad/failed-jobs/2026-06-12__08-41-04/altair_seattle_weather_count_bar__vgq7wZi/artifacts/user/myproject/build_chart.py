import altair as alt
from vega_datasets import data

# URL-based data source — types must be declared explicitly in shorthand
source = data.seattle_weather.url

# Custom categorical color scale
color_domain = ["sun", "fog", "drizzle", "rain", "snow"]
color_range  = ["#e7ba52", "#c7c7c7", "#aec7e8", "#1f77b4", "#9467bd"]

chart = (
    alt.Chart(source)
    .mark_bar()
    .encode(
        y=alt.Y("weather:N", title="Weather Category"),
        x=alt.X("count():Q", title="Number of Days"),
        color=alt.Color(
            "weather:N",
            scale=alt.Scale(domain=color_domain, range=color_range),
            legend=alt.Legend(title="Weather"),
        ),
    )
    .properties(
        title="Seattle Weather: Days per Category",
        width=400,
        height=250,
    )
)

chart.save("chart.html")
print("chart.html written successfully.")
