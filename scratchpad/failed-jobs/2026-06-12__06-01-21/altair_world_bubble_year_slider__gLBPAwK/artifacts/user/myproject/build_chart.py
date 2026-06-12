import altair as alt
import pandas as pd
import json
import vega_datasets


def main():
    # ── Load gapminder data ────────────────────────────────────────────────
    gapminder = vega_datasets.data.gapminder()

    # Compute the fixed population scale domain across all relevant years
    years = list(range(1955, 2006, 5))
    gapminder_filtered = gapminder[gapminder["year"].isin(years)]
    max_pop = int(gapminder_filtered["pop"].max())

    # ── Centroid lookup table (country name → lon/lat) ────────────────────
    centroids = alt.Data(
        values=[
            {"country": "Afghanistan", "longitude": 66.0868, "latitude": 33.8564},
            {"country": "Argentina", "longitude": -65.1752, "latitude": -35.4465},
            {"country": "Australia", "longitude": 134.5026, "latitude": -25.7307},
            {"country": "Austria", "longitude": 14.0752, "latitude": 47.6139},
            {"country": "Bahamas", "longitude": -77.9294, "latitude": 25.5158},
            {"country": "Bangladesh", "longitude": 90.2675, "latitude": 23.8398},
            {"country": "Belgium", "longitude": 4.5816, "latitude": 50.6523},
            {"country": "Bolivia", "longitude": -64.7023, "latitude": -16.2866},
            {"country": "Brazil", "longitude": -53.0893, "latitude": -10.7885},
            {"country": "Canada", "longitude": -98.3078, "latitude": 61.3621},
            {"country": "Chile", "longitude": -71.3826, "latitude": -37.7312},
            {"country": "China", "longitude": 103.8191, "latitude": 36.5618},
            {"country": "Colombia", "longitude": -73.0823, "latitude": 3.9976},
            {"country": "Costa Rica", "longitude": -84.1941, "latitude": 9.6228},
            {"country": "Croatia", "longitude": 16.4041, "latitude": 45.1},
            {"country": "Cuba", "longitude": -79.2393, "latitude": 21.6229},
            {"country": "Dominican Republic", "longitude": -70.5057, "latitude": 18.8956},
            {"country": "Ecuador", "longitude": -78.752, "latitude": -1.4238},
            {"country": "Egypt", "longitude": 29.8726, "latitude": 26.4959},
            {"country": "El Salvador", "longitude": -88.8965, "latitude": 13.7394},
            {"country": "Finland", "longitude": 26.2738, "latitude": 64.4988},
            {"country": "France", "longitude": 2.549, "latitude": 46.5589},
            {"country": "Georgia", "longitude": 43.368, "latitude": 42.1686},
            {"country": "Germany", "longitude": 10.3858, "latitude": 51.106},
            {"country": "Greece", "longitude": 22.9518, "latitude": 39.696},
            {"country": "Haiti", "longitude": -72.6864, "latitude": 19.1494},
            {"country": "Iceland", "longitude": -18.574, "latitude": 64.9313},
            {"country": "India", "longitude": 79.6082, "latitude": 22.8995},
            {"country": "Indonesia", "longitude": 117.2401, "latitude": -2.2156},
            {"country": "Iran", "longitude": 54.3008, "latitude": 32.575},
            {"country": "Iraq", "longitude": 43.7533, "latitude": 33.0465},
            {"country": "Ireland", "longitude": -8.1379, "latitude": 53.1755},
            {"country": "Israel", "longitude": 35.0044, "latitude": 31.4617},
            {"country": "Italy", "longitude": 12.0707, "latitude": 42.7956},
            {"country": "Jamaica", "longitude": -77.3204, "latitude": 18.1569},
            {"country": "Japan", "longitude": 137.1835, "latitude": 37.5924},
            {"country": "Kenya", "longitude": 37.7959, "latitude": 0.5995},
            {"country": "Lebanon", "longitude": 35.8805, "latitude": 33.9211},
            {"country": "Mexico", "longitude": -102.5337, "latitude": 23.9475},
            {"country": "Netherlands", "longitude": 5.5582, "latitude": 52.2396},
            {"country": "New Zealand", "longitude": 171.4849, "latitude": -41.9871},
            {"country": "Nigeria", "longitude": 8.1053, "latitude": 9.5945},
            {"country": "North Korea", "longitude": 127.1927, "latitude": 40.1542},
            {"country": "Norway", "longitude": 10.3463, "latitude": 65.2808},
            {"country": "Pakistan", "longitude": 69.358, "latitude": 29.9966},
            {"country": "Peru", "longitude": -74.3776, "latitude": -9.153},
            {"country": "Philippines", "longitude": 122.8828, "latitude": 12.751},
            {"country": "Poland", "longitude": 19.3901, "latitude": 52.1276},
            {"country": "Portugal", "longitude": -8.5022, "latitude": 39.5955},
            {"country": "Rwanda", "longitude": 29.9203, "latitude": -1.9999},
            {"country": "Saudi Arabia", "longitude": 44.5391, "latitude": 24.1225},
            {"country": "South Africa", "longitude": 25.0839, "latitude": -29.0003},
            {"country": "South Korea", "longitude": 127.832, "latitude": 36.3878},
            {"country": "Spain", "longitude": -3.6492, "latitude": 40.2266},
            {"country": "Switzerland", "longitude": 8.2087, "latitude": 46.7998},
            {"country": "Turkey", "longitude": 35.1787, "latitude": 39.0572},
            {"country": "United Kingdom", "longitude": -2.861, "latitude": 54.1239},
            {"country": "United States", "longitude": -112.4617, "latitude": 45.6795},
            {"country": "Venezuela", "longitude": -66.3524, "latitude": 7.1258},
        ]
    )

    # ── Year slider parameter ─────────────────────────────────────────────
    year_param = alt.param(
        name="Year",
        value=1955,
        bind=alt.binding_range(min=1955, max=2005, step=5, name="Year"),
    )

    # ── Base map layer ────────────────────────────────────────────────────
    base = (
        alt.Chart(alt.topo_feature(vega_datasets.data.world_110m.url, "countries"))
        .mark_geoshape(fill="#eeeeee", stroke="white")
    )

    # ── Bubble layer ──────────────────────────────────────────────────────
    bubbles = (
        alt.Chart(vega_datasets.data.gapminder.url)
        .mark_circle(opacity=0.7, stroke="black", strokeWidth=0.5)
        .transform_lookup(
            lookup="country",
            from_=alt.LookupData(data=centroids, key="country", fields=["longitude", "latitude"]),
        )
        .transform_filter(alt.datum.year == year_param)
        .encode(
            longitude="longitude:Q",
            latitude="latitude:Q",
            size=alt.Size(
                "pop:Q",
                scale=alt.Scale(domain=[0, max_pop]),
                legend=alt.Legend(title="Population"),
            ),
            color=alt.Color("cluster:N", legend=alt.Legend(title="Cluster")),
            tooltip=["country:N", "year:O", "pop:Q", "cluster:N"],
        )
        .add_params(year_param)
    )

    # ── Layer and project ─────────────────────────────────────────────────
    chart = (
        alt.layer(base, bubbles)
        .project(type="naturalEarth1")
        .properties(width=800, height=500, title="World Population Bubble Map")
        .configure_view(strokeWidth=0)
    )

    # ── Save outputs ──────────────────────────────────────────────────────
    chart.save("chart.html")

    with open("spec.json", "w") as f:
        json.dump(chart.to_dict(), f, indent=2)

    print("Saved chart.html and spec.json")


if __name__ == "__main__":
    main()
