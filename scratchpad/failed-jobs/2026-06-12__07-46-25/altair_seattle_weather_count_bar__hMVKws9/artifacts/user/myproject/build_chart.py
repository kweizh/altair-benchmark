import altair as alt
from vega_datasets import data

def main():
    # Use data.seattle_weather.url as the URL-based data source
    source = data.seattle_weather.url

    # Create the horizontal bar chart
    chart = alt.Chart(source).mark_bar().encode(
        y=alt.Y('weather:N', title='Weather Category'),
        x=alt.X('count():Q', title='Count of Days'),
        color=alt.Color(
            'weather:N',
            scale=alt.Scale(
                domain=['sun', 'fog', 'drizzle', 'rain', 'snow'],
                range=['#e7ba52', '#c7c7c7', '#aec7e8', '#1f77b4', '#9467bd']
            ),
            title='Weather'
        )
    )

    # Save the chart as a self-contained HTML file
    chart.save('/home/user/myproject/chart.html')
    print("Chart saved successfully to /home/user/myproject/chart.html")

if __name__ == '__main__':
    main()
