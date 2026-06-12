import altair as alt

# ── Data sources ──────────────────────────────────────────────────────────────
topo_url = alt.datasets.data.us_10m.url
values_url = alt.datasets.data.population_engineers_hurricanes.url

# ── Parameter for metric selection ────────────────────────────────────────────
metric_param = alt.param(
    name="metric",
    value="population",
    bind=alt.binding_select(
        options=["population", "engineers", "hurricanes"],
        name="Metric",
    ),
)

# ── Base chart: TopoJSON states ───────────────────────────────────────────────
base = (
    alt.Chart(topo_url)
    .mark_geoshape(stroke="white")
    .project(type="albersUsa")
    .transform_lookup(
        lookup="id",
        from_=alt.LookupData(
            data=values_url,
            key="id",
            fields=["state", "population", "engineers", "hurricanes"],
        ),
    )
    .transform_calculate(
        # Project the selected metric onto a single field for encoding
        color_value=f"datum[metric]",
    )
    .add_params(metric_param)
)

# ── Color + tooltip encoding ──────────────────────────────────────────────────
choropleth = base.encode(
    color=alt.Color(
        "color_value:Q",
        title=None,
        scale=alt.Scale(scheme="blues"),
    ),
    tooltip=[
        alt.Tooltip("state:N", title="State"),
        alt.Tooltip("color_value:Q", title="Value", format=","),
    ],
)

# ── Persist ───────────────────────────────────────────────────────────────────
choropleth.save("chart.html")
print("✅ chart.html generated successfully.")
