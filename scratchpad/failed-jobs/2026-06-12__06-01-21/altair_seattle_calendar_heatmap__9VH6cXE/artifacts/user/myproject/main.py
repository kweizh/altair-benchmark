import altair as alt
from vega_datasets import data

# ── Data source ──────────────────────────────────────────────────────────────
source = data.seattle_weather.url

# ── Year selection parameter ─────────────────────────────────────────────────
year_param = alt.param(
    name="selected_year",
    bind=alt.binding_select(
        options=[2012, 2013, 2014, 2015],
        name="Select Year: ",
    ),
    value=2012,
)

# ── Opacity condition using when/then/otherwise ──────────────────────────────
opacity_cond = (
    alt.when("datum['year(date)'] == selected_year")
    .then(alt.value(1.0))
    .otherwise(alt.value(0.2))
)

# ── Base chart ───────────────────────────────────────────────────────────────
base = (
    alt.Chart(source, width=260, height=200)
    .mark_rect()
    .encode(
        alt.X("date(date):O")
            .title("Day of Month")
            .axis(labelAngle=0, tickCount=1, grid=True),
        alt.Y("month(date):O")
            .title("Month")
            .axis(format="%b", labelAngle=0),
        alt.Color("sum(precipitation):Q")
            .scale(scheme="greens")
            .title("Precipitation (mm)")
            .legend(orient="bottom"),
        opacity=opacity_cond,
        tooltip=[
            alt.Tooltip(field="date", type="temporal", title="Date"),
            alt.Tooltip(field="precipitation", aggregate="sum", type="quantitative", title="Precipitation (mm)", format=".1f"),
        ],
    )
)

# ── Facet by year ────────────────────────────────────────────────────────────
chart = base.add_params(year_param).facet(
    column=alt.Column("year(date):O")
        .title("Year")
        .header(titleFontWeight="bold"),
    spacing=10,
)

chart = chart.properties(
    title=alt.TitleParams(
        "Seattle Daily Precipitation (Calendar Heatmap)",
        fontSize=18,
        anchor="middle",
    ),
)

# ── Save ─────────────────────────────────────────────────────────────────────
chart.save("chart.html")
print("✅ chart.html generated successfully.")
