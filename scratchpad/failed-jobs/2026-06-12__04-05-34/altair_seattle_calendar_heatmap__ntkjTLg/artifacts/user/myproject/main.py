import altair as alt
from vega_datasets import data

def main():
    # Load Seattle weather data URL
    source = data.seattle_weather.url

    # Create year selection parameter bound to a dropdown
    years = [2012, 2013, 2014, 2015]
    year_dropdown = alt.binding_select(options=years, name='Select Year: ')
    year_select = alt.param(
        name='selected_year',
        value=2012,
        bind=year_dropdown
    )

    # Build the base heatmap chart
    base = alt.Chart(source).mark_rect().encode(
        x=alt.X('date(date):O', title='Day of Month'),
        y=alt.Y('month(date):O', title='Month', axis=alt.Axis(format='%b')),
        color=alt.Color('sum(precipitation):Q', scale=alt.Scale(scheme='greens'), title='Precipitation (mm)'),
        opacity=alt.when('year(datum.date) == selected_year').then(alt.value(1.0)).otherwise(alt.value(0.2)),
        tooltip=[
            alt.Tooltip('date:T', title='Date'),
            alt.Tooltip('sum(precipitation):Q', title='Precipitation (mm)')
        ]
    ).properties(
        width=220,
        height=200
    )

    # Facet the chart by year (column)
    chart = base.facet(
        column=alt.Column('year(date):O', title='Year')
    ).add_params(
        year_select
    ).properties(
        title='Seattle Daily Precipitation (Calendar Heatmap)'
    )

    # Save the chart as a self-contained HTML file
    chart.save('chart.html')
    print("Chart saved successfully to chart.html")

if __name__ == '__main__':
    main()
