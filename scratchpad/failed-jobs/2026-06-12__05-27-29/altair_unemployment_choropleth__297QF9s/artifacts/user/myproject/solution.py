import altair as alt
from vega_datasets import data

# Shared interval brush on the histogram's x-axis
brush = alt.selection_interval(encodings=['x'])

# --- Histogram of unemployment rate ---
histogram = (
    alt.Chart(data.unemployment.url)
    .mark_bar()
    .encode(
        x=alt.X('rate:Q', bin=alt.Bin(maxbins=30)),
        y=alt.Y('count():Q'),
        color=alt.value('steelblue'),
    )
    .add_params(brush)
    .properties(width=600, height=150, title='Unemployment Rate Distribution')
)

# --- County choropleth map ---
counties = alt.topo_feature(data.us_10m.url, 'counties')

choropleth = (
    alt.Chart(counties)
    .mark_geoshape(stroke='white', strokeWidth=0.3)
    .transform_lookup(
        lookup='id',
        from_=alt.LookupData(data.unemployment.url, 'id', ['rate']),
    )
    .transform_filter(brush)
    .encode(
        color=alt.Color(
            'rate:Q',
            scale=alt.Scale(
                type='threshold',
                domain=[0.05, 0.10, 0.15, 0.20],
                scheme='blues',
            ),
            legend=alt.Legend(title='Unemployment Rate'),
        ),
        tooltip=['id:Q', 'rate:Q'],
    )
    .project(type='albersUsa')
    .properties(width=600, height=400, title='US County Unemployment Rate (2018)')
)

# --- Combine into a vertical dashboard ---
chart = alt.vconcat(choropleth, histogram)

# --- Save as interactive HTML ---
chart.save('/home/user/myproject/chart.html')
print('chart.html saved successfully.')