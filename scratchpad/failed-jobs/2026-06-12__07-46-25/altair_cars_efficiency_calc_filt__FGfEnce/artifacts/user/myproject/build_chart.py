import os
import altair as alt
from vega_datasets import data

def build_chart():
    # Define the chart using URL-based data source and explicit encoding types
    chart = alt.Chart(data.cars.url).transform_calculate(
        Efficiency='datum.Miles_per_Gallon / datum.Weight_in_lbs'
    ).transform_filter(
        alt.datum.Efficiency > 0.01
    ).mark_bar().encode(
        x=alt.X('Cylinders:O', sort='ascending'),
        y=alt.Y('Efficiency:Q', aggregate='mean').axis(title='Mean Efficiency (mpg/lb)'),
        color=alt.Color('Cylinders:O').scale(scheme='category10')
    )
    
    # Ensure the output directory exists
    os.makedirs('/home/user/myproject', exist_ok=True)
    
    # Save the chart as a self-contained HTML file
    chart.save('/home/user/myproject/chart.html')
    print("Chart saved successfully to /home/user/myproject/chart.html")

if __name__ == '__main__':
    build_chart()
