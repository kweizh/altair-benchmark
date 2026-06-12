import altair as alt
from vega_datasets import data

# Create the interval brush selection on the x-axis (rate)
brush = alt.selection_interval(encodings=["x"])

# --- Histogram (bottom chart) ---
# Reads directly from unemployment data; all counties always visible
histogram = (
    alt.Chart(data.unemployment.url)
    .mark_bar()
    .encode(
        x=alt.X("rate:Q", bin=True, title="Unemployment Rate"),
        y=alt.Y("count():Q", title="Number of Counties"),
        color=alt.condition(brush, alt.value("steelblue"), alt.value("lightgray")),
    )
    .add_params(brush)
    .properties(width=800, height=150, title="Unemployment Rate Distribution (brush to filter map)")
)

# --- Choropleth map (top chart) ---
choropleth = (
    alt.Chart(alt.topo_feature(data.us_10m.url, "counties"))
    .mark_geoshape()
    .transform_lookup(
        lookup="id",
        from_=alt.LookupData(data=data.unemployment.url, key="id", fields=["rate"]),
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
            legend=alt.Legend(title="Unemployment Rate"),
        ),
        tooltip=[
            alt.Tooltip("id:O", title="County FIPS"),
            alt.Tooltip("rate:Q", title="Unemployment Rate", format=".1%"),
        ],
    )
    .project(type="albersUsa")
    .properties(width=800, height=500, title="US County Unemployment Rate (2018)")
)

# --- Combine into a vertically concatenated dashboard ---
chart = alt.vconcat(choropleth, histogram).resolve_scale(color="independent")

# Save as interactive HTML
chart.save("chart.html")
print("chart.html written successfully.")
