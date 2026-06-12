import altair as alt
import json
import os

# Data source
url = "https://vega.github.io/vega-datasets/data/population.json"

years = [1850, 1860, 1870, 1880, 1890, 1900, 1910, 1920, 1930, 1940, 1950, 1960, 1970, 1980, 1990, 2000]
year_slider = alt.binding_select(options=years, name='Year ')
year_param = alt.param(name='year', value=1980, bind=year_slider)

chart = alt.Chart(url).mark_bar().encode(
    y=alt.Y('age:O', sort='descending', title='Age'),
    x=alt.X('signed_people:Q', title='Population', 
            axis=alt.Axis(format='s', labelExpr='abs(datum.value)')),
    color=alt.Color('sex:N', 
                    scale=alt.Scale(domain=[1, 2], range=['steelblue', 'salmon']),
                    legend=alt.Legend(title='Sex', labelExpr="datum.value == 1 ? 'Male' : 'Female'"))
).transform_calculate(
    signed_people="datum.sex == 1 ? -datum.people : datum.people"
).transform_filter(
    alt.datum.year == year_param
).add_params(
    year_param
).properties(
    width=600,
    height=400,
    title='US Population by Age and Sex'
)

chart.save("/home/user/myproject/pyramid.html")

with open("/home/user/myproject/pyramid_spec.json", "w") as f:
    json.dump(chart.to_dict(), f, indent=2)
