import altair as alt
from vega_datasets import data

# Use the URL-based data source (no inline data transfer)
source = data.barley.url

chart = (
    alt.Chart(source)
    .mark_bar()
    .encode(
        y=alt.Y(
            "site:N",
            sort=alt.EncodingSortField(field="yield", op="mean", order="descending"),
            title="Site",
        ),
        x=alt.X("mean(yield):Q", title="Mean Yield"),
        color=alt.Color("year:N", title="Year"),
        yOffset=alt.YOffset("year:N"),
    )
    .properties(
        title="Mean Barley Yield by Site and Year",
        width=500,
        height=300,
    )
)

output_path = "/home/user/myproject/chart.html"
chart.save(output_path)
print(f"Chart saved to {output_path}")
