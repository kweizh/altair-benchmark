import altair as alt
from vega_datasets import data

def build_chart():
    # Load the TopoJSON states feature collection
    states = alt.topo_feature(data.us_10m.url, feature='states')

    # Define the interactive dropdown control
    metric_select = alt.binding_select(
        options=['population', 'engineers', 'hurricanes'],
        name='Select Metric: '
    )
    metric_param = alt.param(
        name='metric',
        value='population',
        bind=metric_select
    )

    # Build the choropleth map chart
    chart = alt.Chart(states).mark_geoshape(
        stroke='white',
        strokeWidth=0.5
    ).project(
        type='albersUsa'
    ).transform_lookup(
        lookup='id',
        from_=alt.LookupData(
            data=data.population_engineers_hurricanes.url,
            key='id',
            fields=['state', 'population', 'engineers', 'hurricanes']
        )
    ).transform_calculate(
        selected_value="datum[metric]"
    ).encode(
        color=alt.Color('selected_value:Q', title='Metric Value'),
        tooltip=[
            alt.Tooltip('state:N', title='State'),
            alt.Tooltip('selected_value:Q', title='Value', format=',')
        ]
    ).add_params(
        metric_param
    ).properties(
        width=800,
        height=500,
        title="Interactive US State Choropleth Map"
    )

    # Save the chart as a self-contained HTML file
    chart.save('/home/user/altair_choropleth_app/chart.html')
    print("Chart successfully generated and saved to /home/user/altair_choropleth_app/chart.html")

if __name__ == "__main__":
    build_chart()
