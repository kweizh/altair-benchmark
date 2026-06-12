import altair as alt
from vega_datasets import data

def build_chart():
    # Define the range slider binding
    slider = alt.binding_range(
        min=50,
        max=250,
        step=10,
        name='HP threshold: '
    )
    
    # Define the parameter representing the live threshold
    hp_threshold = alt.param(
        name='hp_threshold',
        value=150,
        bind=slider
    )
    
    # Build the scatter plot chart
    chart = alt.Chart(data.cars.url).mark_point().encode(
        x='Horsepower:Q',
        y='Miles_per_Gallon:Q',
        color=alt.condition(
            alt.datum.Horsepower < hp_threshold,
            alt.value('steelblue'),
            alt.value('orange')
        )
    ).add_params(
        hp_threshold
    ).properties(
        title='MPG vs Horsepower (threshold)'
    )
    
    # Save the resulting chart as a self-contained HTML file
    chart.save('/home/user/myproject/chart.html')
    print("Successfully built and saved chart to /home/user/myproject/chart.html")

if __name__ == '__main__':
    build_chart()
