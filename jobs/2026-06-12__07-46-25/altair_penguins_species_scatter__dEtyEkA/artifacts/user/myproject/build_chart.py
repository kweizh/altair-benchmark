import altair as alt
import vega_datasets
from vega_datasets.core import Dataset, DataLoader

# Monkeypatch vega_datasets to support the penguins dataset
Dataset._dataset_info['penguins'] = {
    'filename': 'penguins.json',
    'format': 'json',
    'is_local': False
}
DataLoader._datasets['penguins'] = 'penguins'

original_init = Dataset.__init__
def new_init(self, name):
    original_init(self, name)
    if name == 'penguins':
        # Use a stable URL that contains the penguins dataset
        self.url = 'https://cdn.jsdelivr.net/npm/vega-datasets@v2.0.0/data/penguins.json'

Dataset.__init__ = new_init

def main():
    # Use vega_datasets.data.penguins.url as the data source
    from vega_datasets import data
    penguins_url = data.penguins.url

    # Build the chart
    chart = alt.Chart(penguins_url).mark_point(
        filled=True,
        size=80
    ).encode(
        x=alt.X('Flipper Length (mm):Q', scale=alt.Scale(zero=False)),
        y=alt.Y('Body Mass (g):Q', scale=alt.Scale(zero=False)),
        color=alt.Color('Species:N'),
        shape=alt.Shape('Sex:N'),
        tooltip=[
            alt.Tooltip('Species:N'),
            alt.Tooltip('Island:N'),
            alt.Tooltip('Flipper Length (mm):Q'),
            alt.Tooltip('Body Mass (g):Q')
        ]
    ).interactive()

    # Save the chart as chart.html
    chart.save('/home/user/myproject/chart.html')
    print("Chart saved successfully to /home/user/myproject/chart.html")

if __name__ == '__main__':
    main()
