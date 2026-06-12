import altair as alt
from vega_datasets import data

source = data.seattle_weather.url

# Year dropdown parameter
years = [2012, 2013, 2014, 2015]
year_bind = alt.binding_select(options=years, name="Year: ")
year_param = alt.param(name="year_select", bind=year_bind, value=2012)

chart = (
    alt.Chart(source)
    .mark_rect()
    .encode(
        x=alt.X("date(date):O", title="Day of Month"),
        y=alt.Y(
            "month(date):O",
            title="Month",
            axis=alt.Axis(
                labelExpr="['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'][datum.value]"
            ),
        ),
        color=alt.Color(
            "sum(precipitation):Q",
            scale=alt.Scale(scheme="greens"),
            title="Precipitation",
        ),
        opacity=alt.when(year_param == alt.datum.year_date)
        .then(alt.value(1))
        .otherwise(alt.value(0.2)),
        tooltip=[
            alt.Tooltip("date:T", title="Date"),
            alt.Tooltip("sum(precipitation):Q", title="Precipitation"),
        ],
    )
    .add_params(year_param)
    .facet(column="year(date):O")
    .properties(
        title="Seattle Daily Precipitation (Calendar Heatmap)"
    )
)

chart.save("/home/user/myproject/chart.html")