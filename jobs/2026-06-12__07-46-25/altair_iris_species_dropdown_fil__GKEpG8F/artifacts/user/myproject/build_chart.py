import altair as alt
from vega_datasets import data

def build_chart():
    # Use data.iris.url as the data source
    source = data.iris.url

    # Define a single bound input parameter using alt.binding_select
    species_dropdown = alt.binding_select(
        options=['setosa', 'versicolor', 'virginica'],
        name='Species: '
    )

    # Bind that input to a parameter created with alt.param(...)
    # Initialize with 'setosa'
    species_param = alt.param(
        name='selected_species',
        value='setosa',
        bind=species_dropdown
    )

    # Build the scatter plot
    chart = alt.Chart(source).mark_point().encode(
        x='sepalLength:Q',
        y='sepalWidth:Q',
        color=alt.when('datum.species == selected_species')
                 .then('species:N')
                 .otherwise(alt.value('lightgray'))
    ).add_params(species_param)

    # Save the resulting chart as a single self-contained HTML file
    chart.save('/home/user/myproject/chart.html')

if __name__ == '__main__':
    build_chart()
