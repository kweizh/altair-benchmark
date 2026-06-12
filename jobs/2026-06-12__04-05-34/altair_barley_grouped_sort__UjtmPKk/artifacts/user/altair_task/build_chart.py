"""Build the barley grouped-bar chart HTML.

This script constructs the required Altair chart and writes it to
``/home/user/altair_task/output/chart.html``.
"""

import os
import altair as alt
from vega_datasets import data


def main() -> None:
    output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")
    os.makedirs(output_dir, exist_ok=True)

    # 1. Define the bar layer
    bar_layer = alt.Chart().mark_bar().encode(
        x=alt.X(
            'site:N',
            sort=alt.EncodingSortField(field='yield', op='mean', order='descending'),
            title='Site'
        ),
        y=alt.Y(
            'yield:Q',
            aggregate='mean',
            title='Mean Yield'
        ),
        xOffset=alt.XOffset(
            'variety:N',
            title='Variety'
        ),
        color=alt.Color(
            'variety:N',
            scale=alt.Scale(scheme='tableau10'),
            title='Variety'
        )
    )

    # 2. Define the tick layer with aggregate transform inside the spec
    tick_layer = alt.Chart().mark_tick(
        color='black',
        size=25,
        thickness=3
    ).encode(
        x=alt.X(
            'site:N',
            sort=alt.EncodingSortField(field='yield', op='mean', order='descending')
        ),
        y=alt.Y(
            'mean_yield:Q'
        )
    ).transform_aggregate(
        mean_yield='mean(yield)',
        groupby=['site', 'year']
    )

    # 3. Layer the bar and tick charts, bind the barley dataset, and facet by year
    chart = alt.layer(
        bar_layer,
        tick_layer,
        data=data.barley.url
    ).facet(
        facet=alt.Facet('year:O', title='Year')
    ).properties(
        title=alt.TitleParams(
            text='Barley Yield by Site and Variety',
            subtitle='Grouped bar chart showing mean yield per site/variety, with black ticks representing the per-site mean yield'
        )
    )

    # 4. Save the chart as a self-contained HTML file
    output_path = os.path.join(output_dir, "chart.html")
    chart.save(output_path)
    print(f"Chart successfully saved to {output_path}")


if __name__ == "__main__":
    main()
