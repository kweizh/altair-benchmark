"""Build a back-to-back population age pyramid with Vega-Altair.

Saves `pyramid.html` and `pyramid_spec.json` to /home/user/myproject.
"""

import json

import altair as alt


def main() -> None:
    # Use the URL from altair.datasets so the spec embeds a remote reference
    source_url: str = alt.datasets.data.population.url

    # -- Year dropdown parameter -------------------------------------------
    year_param = alt.param(
        name="year",
        value=1980,
        bind=alt.binding_select(
            name="Census Year",
            options=[
                1850, 1860, 1870, 1880, 1890, 1900,
                1910, 1920, 1930, 1940, 1950, 1960,
                1970, 1980, 1990, 2000,
            ],
        ),
    )

    # -- Base chart --------------------------------------------------------
    base = (
        alt.Chart(source_url)
        .mark_bar()
        .encode(
            x=alt.X(
                "signed_people:Q",
                axis=alt.Axis(
                    title="Population",
                    format="~s",
                    labelExpr="abs(datum.value)",
                ),
            ),
            y=alt.Y(
                "age:O",
                sort="descending",
                axis=alt.Axis(title="Age"),
            ),
            color=alt.Color(
                "sex:N",
                scale=alt.Scale(domain=[1, 2], range=["steelblue", "salmon"]),
                legend=alt.Legend(
                    title="Sex",
                    labelExpr="datum.value == 1 ? 'Male' : 'Female'",
                ),
            ),
        )
        .transform_calculate(
            signed_people="datum.sex == 1 ? -datum.people : datum.people",
        )
        .transform_filter(year_param)
        .add_params(year_param)
        .properties(
            title="US Population Age Pyramid",
            width=600,
            height=500,
        )
    )

    # -- Save outputs ------------------------------------------------------
    output_dir = "/home/user/myproject"

    # HTML file (self-contained)
    base.save(f"{output_dir}/pyramid.html")

    # Raw Vega-Lite spec as JSON
    spec = base.to_dict()
    with open(f"{output_dir}/pyramid_spec.json", "w") as f:
        json.dump(spec, f, indent=2)


if __name__ == "__main__":
    main()
