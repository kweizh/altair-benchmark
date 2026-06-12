import os
import altair as alt
from vega_datasets import data


def main() -> None:
    # Use the TopoJSON counties dataset as the primary geographic data source
    counties = alt.topo_feature(data.us_10m.url, "counties")

    # Create the interval brush selection on the x-axis for the histogram
    brush = alt.selection_interval(name="brush", encodings=["x"])

    # Create the choropleth map.
    # Note: We use a query parameter '?lookup' on the lookup data URL to trick
    # Vega-Lite's optimizer into keeping it as a separate dataset in the
    # compiled Vega spec. This avoids the 'Undefined data set name: source_1'
    # bug in Vega-Lite when concatenating charts with identical data sources.
    map_chart = (
        alt.Chart(counties)
        .mark_geoshape()
        .transform_lookup(
            lookup="id",
            from_=alt.LookupData(
                data=alt.UrlData(
                    url=data.unemployment.url + "?lookup",
                    format=alt.DataFormat(type="tsv"),
                ),
                key="id",
                fields=["rate"],
            ),
        )
        .transform_filter(brush)
        .encode(
            color=alt.Color(
                "rate:Q",
                scale=alt.Scale(
                    type="threshold",
                    domain=[0.05, 0.10, 0.15, 0.20],
                    scheme="blues",
                ),
            ),
            tooltip=["id:O", "rate:Q"],
        )
        .project(type="albersUsa")
    )

    # Create the brushable histogram
    histogram = (
        alt.Chart(data.unemployment.url)
        .mark_bar()
        .encode(x=alt.X("rate:Q", bin=True), y="count()")
        .add_params(brush)
    )

    # Combine the charts using vertical concatenation
    chart = alt.vconcat(map_chart, histogram)

    # Save the final chart as an interactive HTML file
    output_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "chart.html"
    )
    chart.save(output_path)
    print(f"Chart successfully saved to {output_path}")


if __name__ == "__main__":
    main()
