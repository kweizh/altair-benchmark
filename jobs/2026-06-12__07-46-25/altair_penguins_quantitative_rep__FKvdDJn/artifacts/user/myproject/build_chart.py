import altair as alt
import vega_datasets

# Dynamically patch vega_datasets to support 'penguins'
vega_datasets.core.Dataset._dataset_info['penguins'] = {
    'filename': 'penguins.json',
    'format': 'json',
    'is_local': False
}
vega_datasets.data._datasets['penguins'] = 'penguins'

from vega_datasets import data

def build_chart():
    # Use data.penguins.url from vega_datasets
    source = data.penguins.url

    # Create the repeated scatter plot matrix (SPLOM)
    chart = alt.Chart(source).mark_point().encode(
        x=alt.X(alt.repeat('column'), type='quantitative', scale=alt.Scale(zero=False)),
        y=alt.Y(alt.repeat('row'), type='quantitative', scale=alt.Scale(zero=False)),
        color='Species:N'
    ).properties(
        width=180,
        height=180
    ).repeat(
        row=['Body Mass (g)', 'Flipper Length (mm)'],
        column=['Beak Length (mm)', 'Beak Depth (mm)']
    )

    # Save the chart as a self-contained HTML file
    chart.save('/home/user/myproject/chart.html')

if __name__ == '__main__':
    build_chart()
