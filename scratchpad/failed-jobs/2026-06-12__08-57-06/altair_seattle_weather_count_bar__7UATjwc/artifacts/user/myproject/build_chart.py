import altair as alt
from vega_datasets import data

chart = (
    alt.Chart(data.seattle_weather.url)
    .mark_bar()
    .encode(
        alt.X("count()", title="Number of Days"),
        alt.Y("weather:N", title="Weather"),
        alt.Color(
            "weather:N",
            scale=alt.Scale(
                domain=["sun", "fog", "drizzle", "rain", "snow"],
                range=["#e7ba52", "#c7c7c7", "#aec7e8", "#1f77b4", "#9467bd"],
            ),
            title="Weather",
        ),
    )
)

chart.save("chart.html")
