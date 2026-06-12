import altair as alt
from vega_datasets import data
import pandas as pd
import json

def main():
    # Load gapminder to find the max population for the scale domain
    gapminder_url = data.gapminder.url
    gapminder_df = data.gapminder()
    max_pop = float(gapminder_df['pop'].max())

    # Create a small inline lookup table for centroids
    centroids = pd.DataFrame([
        {"country": "Afghanistan", "lon": 65.0, "lat": 33.0},
        {"country": "Argentina", "lon": -64.0, "lat": -34.0},
        {"country": "Australia", "lon": 133.0, "lat": -27.0},
        {"country": "Austria", "lon": 13.3, "lat": 47.5},
        {"country": "Bangladesh", "lon": 90.0, "lat": 24.0},
        {"country": "Belgium", "lon": 4.0, "lat": 50.0},
        {"country": "Bolivia", "lon": -65.0, "lat": -17.0},
        {"country": "Brazil", "lon": -55.0, "lat": -10.0},
        {"country": "Canada", "lon": -106.0, "lat": 56.0},
        {"country": "China", "lon": 105.0, "lat": 35.0},
        {"country": "France", "lon": 2.0, "lat": 46.0},
        {"country": "Germany", "lon": 9.0, "lat": 51.0},
        {"country": "India", "lon": 79.0, "lat": 22.0},
        {"country": "Japan", "lon": 138.0, "lat": 36.0},
        {"country": "Mexico", "lon": -102.0, "lat": 23.0},
        {"country": "Nigeria", "lon": 8.0, "lat": 10.0},
        {"country": "South Africa", "lon": 24.0, "lat": -29.0},
        {"country": "United Kingdom", "lon": -2.0, "lat": 54.0},
        {"country": "United States", "lon": -97.0, "lat": 38.0}
    ])

    # Base layer: TopoJSON countries
    world = alt.topo_feature(data.world_110m.url, 'countries')
    base = alt.Chart(world).mark_geoshape(
        fill='#eeeeee',
        stroke='white'
    )

    # Year slider parameter
    year_slider = alt.param(
        name='Year',
        value=1955,
        bind=alt.binding_range(min=1955, max=2005, step=5, name='Year')
    )

    # Overlay: gapminder bubbles
    bubbles = alt.Chart(gapminder_url).mark_circle().transform_lookup(
        lookup='country',
        from_=alt.LookupData(data=centroids, key='country', fields=['lon', 'lat'])
    ).transform_filter(
        alt.datum.year == year_slider
    ).encode(
        longitude='lon:Q',
        latitude='lat:Q',
        size=alt.Size('pop:Q', scale=alt.Scale(domain=[0, max_pop])),
        color='cluster:N'
    )

    # Combine layers and set projection
    chart = alt.layer(base, bubbles).project(
        type='naturalEarth1'
    ).add_params(
        year_slider
    ).properties(
        width=800,
        height=400,
        title="World Population Bubble Map"
    )

    # Save to HTML
    chart.save('chart.html')

    # Save to JSON
    with open('spec.json', 'w') as f:
        json.dump(chart.to_dict(), f, indent=2)

if __name__ == '__main__':
    main()
