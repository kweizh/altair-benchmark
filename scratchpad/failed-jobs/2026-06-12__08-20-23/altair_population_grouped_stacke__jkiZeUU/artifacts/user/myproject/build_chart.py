import altair as alt
from vega_datasets import data

chart = (
    alt.Chart(data.population.url)
    .transform_calculate(
        age_group="datum.age < 20 ? '0-19' : datum.age < 40 ? '20-39' : datum.age < 60 ? '40-59' : '60+'"
    )
    .transform_aggregate(
        people='sum(people)',
        groupby=['year', 'age_group']
    )
    .mark_area()
    .encode(
        x=alt.X('year:O'),
        y=alt.Y('sum(people):Q').stack('normalize'),
        color=alt.Color(
            'age_group:N',
            sort=['0-19', '20-39', '40-59', '60+'],
            scale=alt.Scale(scheme='tableau10')
        )
    )
    .properties(
        width=700,
        height=350,
        title='US Population Composition (Normalized)'
    )
)

chart.save('/home/user/myproject/chart.html')