import altair as alt
from vega_datasets import data

# Use URL-based data source
source = data.seattle_weather.url

# Define custom color mapping
weather_domain = ['sun', 'fog', 'drizzle', 'rain', 'snow']
weather_range = ['#e7ba52', '#c7c7c7', '#aec7e8', '#1f77b4', '#9467bd']

# Build a single horizontal bar chart counting days per weather category
chart = (
    alt.Chart(source)
    .mark_bar()
    .encode(
        y=alt.Y('weather:N'),
        x=alt.X('count():Q'),
        color=alt.Color(
            'weather:N',
            scale=alt.Scale(domain=weather_domain, range=weather_range),
        ),
    )
)

# Save as self-contained HTML
chart.save('chart.html')