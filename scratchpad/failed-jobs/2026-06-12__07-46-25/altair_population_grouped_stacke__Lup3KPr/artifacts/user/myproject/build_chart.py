import altair as alt
import vega_datasets

def build_chart():
    # Use vega_datasets.data.population.url as the data source
    data_url = vega_datasets.data.population.url

    # Create the chart
    chart = alt.Chart(data_url).mark_area().encode(
        x=alt.X('year:O'),
        y=alt.Y('sum(people):Q', stack='normalize'),
        color=alt.Color(
            'age_group:N',
            sort=['0-19', '20-39', '40-59', '60+'],
            scale=alt.Scale(scheme='tableau10')
        )
    ).transform_calculate(
        age_group="datum.age < 20 ? '0-19' : datum.age < 40 ? '20-39' : datum.age < 60 ? '40-59' : '60+'"
    ).transform_aggregate(
        people='sum(people)',
        groupby=['year', 'age_group']
    ).properties(
        width=700,
        height=350,
        title='US Population Composition (Normalized)'
    )

    # Save the chart to /home/user/myproject/chart.html
    chart.save('/home/user/myproject/chart.html')
    print("Chart saved successfully to /home/user/myproject/chart.html")

if __name__ == '__main__':
    build_chart()
