import altair as alt
from vega_datasets import data

# Use the URL so the spec references it rather than inlining the full table
source = data.seattle_weather.url

# Bound year parameter with a dropdown (options: all four years in the dataset)
year_param = alt.param(
    name="selected_year",
    value=2012,
    bind=alt.binding_select(
        options=[2012, 2013, 2014, 2015],
        name="Year: ",
    ),
)

# Calendar heatmap: day-of-month (x) × month (y), colored by total precipitation
heatmap = (
    alt.Chart(source)
    .mark_rect()
    .encode(
        x=alt.X(
            "date(date):O",
            title="Day of Month",
            axis=alt.Axis(labelAngle=0),
        ),
        y=alt.Y(
            "month(date):O",
            title="Month",
            axis=alt.Axis(
                labelExpr=(
                    "['Jan','Feb','Mar','Apr','May','Jun',"
                    "'Jul','Aug','Sep','Oct','Nov','Dec'][datum.value - 1]"
                )
            ),
        ),
        color=alt.Color(
            "sum(precipitation):Q",
            scale=alt.Scale(scheme="greens"),
            title="Total Precipitation (mm)",
        ),
        opacity=alt.when(
            alt.expr.year(alt.expr.toDate(alt.datum["date"])) == year_param
        )
        .then(alt.value(1.0))
        .otherwise(alt.value(0.2)),
        tooltip=[
            alt.Tooltip("date:T", title="Date"),
            alt.Tooltip("sum(precipitation):Q", title="Total Precipitation (mm)"),
        ],
    )
    .add_params(year_param)
    .properties(width=420, height=220)
    .facet(
        column=alt.Column(
            "year(date):O",
            title="Year",
            header=alt.Header(titleOrient="bottom", labelOrient="bottom"),
        )
    )
    .properties(title="Seattle Daily Precipitation (Calendar Heatmap)")
    .configure_title(fontSize=18, anchor="middle")
    .configure_axis(labelFontSize=11, titleFontSize=12)
    .configure_header(labelFontSize=13)
)

heatmap.save("chart.html")
print("Saved chart.html")
