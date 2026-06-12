import altair as alt
from vega_datasets import data

def build_chart():
    # Load barley dataset url
    barley_url = data.barley.url
    
    # Build a horizontal grouped bar chart
    chart = alt.Chart(barley_url).mark_bar().encode(
        y=alt.Y(
            'site:N',
            sort=alt.EncodingSortField(
                field='yield',
                op='mean',
                order='descending'
            )
        ),
        x=alt.X(
            'yield:Q',
            aggregate='mean'
        ),
        color=alt.Color('year:N'),
        yOffset=alt.YOffset('year:N')
    )
    
    # Save the resulting chart as a self-contained HTML file
    chart.save('/home/user/myproject/chart.html')
    print("Successfully built and saved chart to /home/user/myproject/chart.html")

if __name__ == '__main__':
    build_chart()
