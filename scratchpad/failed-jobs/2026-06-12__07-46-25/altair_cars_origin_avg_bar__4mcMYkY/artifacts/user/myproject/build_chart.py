import altair as alt
from vega_datasets import data

def main():
    # Use URL-based data source
    source = data.cars.url
    
    # Create the Altair chart
    chart = alt.Chart(source).mark_bar().encode(
        x=alt.X('Origin:N').sort(field='Miles_per_Gallon', op='mean', order='descending'),
        y='mean(Miles_per_Gallon):Q',
        tooltip=[
            alt.Tooltip('mean(Miles_per_Gallon):Q'),
            alt.Tooltip('count():Q')
        ]
    )
    
    # Save the chart to HTML
    output_path = '/home/user/myproject/chart.html'
    chart.save(output_path)
    print(f"Chart successfully saved to {output_path}")

if __name__ == '__main__':
    main()
