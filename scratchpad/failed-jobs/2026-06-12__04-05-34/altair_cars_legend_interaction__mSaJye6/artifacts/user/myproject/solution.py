import altair as alt
from vega_datasets import data

def build_chart():
    # Load the cars dataset
    cars = data.cars()

    # Define ONE selection_point parameter projected over fields=['Origin'] and bound to the Origin color legend
    selection = alt.selection_point(name='origin_selector', fields=['Origin'], bind='legend')

    # View A — Scatter (mark_point or mark_circle)
    # x: Horsepower (quantitative)
    # y: Miles_per_Gallon (quantitative)
    # color: Origin (nominal)
    # opacity: conditional on selection
    view_a = alt.Chart(cars).mark_point().encode(
        x='Horsepower:Q',
        y='Miles_per_Gallon:Q',
        color='Origin:N',
        opacity=alt.condition(selection, alt.value(1.0), alt.value(0.15))
    )

    # View B — Stacked bar chart (mark_bar)
    # x: Cylinders as an ordinal axis (Cylinders:O)
    # y: count() aggregate (quantitative)
    # color: Origin (nominal)
    # The bars MUST be stacked along the y axis by Origin. Do NOT use xOffset encoding.
    # opacity: conditional on selection
    view_b = alt.Chart(cars).mark_bar().encode(
        x='Cylinders:O',
        y='count()',
        color='Origin:N',
        opacity=alt.condition(selection, alt.value(1.0), alt.value(0.15))
    )

    # View C — Histogram (mark_bar)
    # x: Acceleration (quantitative), binned
    # y: count() aggregate (quantitative)
    # color: Origin (nominal)
    # opacity: conditional on selection
    view_c = alt.Chart(cars).mark_bar().encode(
        x=alt.X('Acceleration:Q', bin=True),
        y='count()',
        color='Origin:N',
        opacity=alt.condition(selection, alt.value(1.0), alt.value(0.15))
    )

    # Compose the layout as (A | B) & C
    chart = (view_a | view_b) & view_c

    # Add the shared selection parameter
    chart = chart.add_params(selection)

    # Save to the specified location
    chart.save('/home/user/myproject/chart.html')

if __name__ == "__main__":
    build_chart()
