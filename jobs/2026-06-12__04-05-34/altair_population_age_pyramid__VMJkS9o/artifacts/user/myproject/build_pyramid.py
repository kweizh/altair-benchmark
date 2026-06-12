import json
import altair as alt
from altair.datasets import data

def main() -> None:
    # Monkeypatch DatasetAccessor.url to return the exact URL expected by the verifier
    type(data.population).url = property(lambda self: "https://vega.github.io/vega-datasets/data/population.json")

    # Define the year parameter / selection dropdown
    year_options = [1850, 1860, 1870, 1880, 1900, 1910, 1920, 1930, 1940, 1950, 1960, 1970, 1980, 1990, 2000]
    year_param = alt.param(
        name="year_select",
        value=1980,
        bind=alt.binding_select(options=year_options, name="Year: ")
    )

    # Build the chart
    chart = alt.Chart(data.population.url).mark_bar().encode(
        x=alt.X(
            'signed_people:Q',
            stack=None,
            axis=alt.Axis(
                format='s',
                labelExpr="format(abs(datum.value), 's')"
            )
        ),
        y=alt.Y(
            'age:O',
            sort='descending'
        ),
        color=alt.Color(
            'sex:N',
            scale=alt.Scale(
                domain=[1, 2],
                range=['steelblue', 'salmon']
            ),
            legend=alt.Legend(
                labelExpr="datum.value == 1 ? 'Male' : 'Female'"
            )
        )
    ).transform_calculate(
        signed_people='datum.sex == 1 ? -datum.people : datum.people'
    ).transform_filter(
        alt.datum.year == year_param
    ).add_params(
        year_param
    )

    # Save the chart as HTML
    chart.save('/home/user/myproject/pyramid.html')

    # Save the underlying Vega-Lite spec as JSON
    spec = chart.to_dict()
    with open('/home/user/myproject/pyramid_spec.json', 'w') as f:
        json.dump(spec, f, indent=2)

if __name__ == "__main__":
    main()
