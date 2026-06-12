import altair as alt
from vega_datasets import data

def main() -> None:
    # Load the classic cars dataset
    cars = data.cars()

    # Define the interval brush selection over both x and y channels
    brush = alt.selection_interval(encodings=['x', 'y'])

    # View A: Scatter plot of Horsepower vs Miles_per_Gallon, colored by Origin
    view_a = alt.Chart(cars).mark_point().encode(
        x='Horsepower:Q',
        y='Miles_per_Gallon:Q',
        color='Origin:N'
    ).add_params(
        brush
    )

    # View B: Horizontal bar chart showing counts by Origin, filtered by View A's brush
    view_b = alt.Chart(cars).mark_bar().encode(
        y='Origin:N',
        x='count():Q'
    ).transform_filter(
        brush
    )

    # View C: Binned 2D heatmap of Weight_in_lbs vs Acceleration, filtered by View A's brush
    view_c = alt.Chart(cars).mark_rect().encode(
        x=alt.X('Weight_in_lbs:Q').bin(),
        y=alt.Y('Acceleration:Q').bin(),
        color='count():Q'
    ).transform_filter(
        brush
    )

    # Compose the dashboard using (A | B) & C
    chart = (view_a | view_b) & view_c

    # Save the chart as an HTML file
    chart.save('/home/user/myproject/chart.html')

if __name__ == '__main__':
    main()
