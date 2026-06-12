import altair as alt
from vega_datasets import data

def main():
    source = data.seattle_weather.url

    year_dropdown = alt.binding_select(
        options=[2012, 2013, 2014, 2015],
        name="Select Year: "
    )
    year_param = alt.param(
        name="YearSelection",
        bind=year_dropdown,
        value=2012
    )

    base = alt.Chart(source).mark_rect().encode(
        x=alt.X('date(date):O', title='Day of Month'),
        y=alt.Y('month(date):O', title='Month'),
        color=alt.Color('sum(precipitation):Q', scale=alt.Scale(scheme='greens'), title='Precipitation'),
        opacity=alt.when(
            alt.datum.year_val == year_param
        ).then(
            alt.value(1.0)
        ).otherwise(
            alt.value(0.2)
        ),
        tooltip=[
            alt.Tooltip('date:T', title='Date'),
            alt.Tooltip('sum(precipitation):Q', title='Precipitation')
        ]
    ).transform_calculate(
        year_val="year(datum.date)"
    ).add_params(
        year_param
    ).properties(
        width=300,
        height=150
    )

    chart = base.facet(
        facet=alt.Facet('year(date):O', title='Year'),
        columns=2
    ).properties(
        title='Seattle Daily Precipitation (Calendar Heatmap)'
    )

    chart.save('chart.html')

if __name__ == '__main__':
    main()
