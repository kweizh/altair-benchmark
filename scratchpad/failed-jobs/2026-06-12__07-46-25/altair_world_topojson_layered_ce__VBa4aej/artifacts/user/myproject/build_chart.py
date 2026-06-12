import altair as alt
import pandas as pd
from vega_datasets import data

def main():
    # Load world countries TopoJSON
    countries = alt.topo_feature(data.world_110m.url, 'countries')

    # Build inline DataFrame of cities
    cities_df = pd.DataFrame({
        'city': ['Tokyo', 'London', 'New York', 'Sao Paulo', 'Sydney'],
        'lat': [35.6762, 51.5074, 40.7128, -23.5505, -33.8688],
        'lon': [139.6503, -0.1278, -74.0060, -46.6333, 151.2093]
    })

    # Layer 1: Country shapes
    background = alt.Chart(countries).mark_geoshape(
        fill='#e8e8e8',
        stroke='white'
    )

    # Layer 2: City circle markers
    points = alt.Chart(cities_df).mark_circle(
        color='red',
        size=80
    ).encode(
        longitude='lon:Q',
        latitude='lat:Q'
    )

    # Layer 3: City text labels
    labels = alt.Chart(cities_df).mark_text(
        dy=-12
    ).encode(
        longitude='lon:Q',
        latitude='lat:Q',
        text='city:N'
    )

    # Layered chart with projection and properties
    chart = alt.layer(background, points, labels).project(
        type='naturalEarth1'
    ).properties(
        width=800,
        height=500
    )

    # Save to self-contained HTML
    chart.save('/home/user/myproject/chart.html')
    print("Chart saved successfully to /home/user/myproject/chart.html")

if __name__ == '__main__':
    main()
