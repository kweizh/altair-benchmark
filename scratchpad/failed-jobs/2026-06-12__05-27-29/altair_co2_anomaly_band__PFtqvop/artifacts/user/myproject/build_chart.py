import altair as alt
from vega_datasets import data
import logging

# Set up logging
logging.basicConfig(
    filename='/home/user/myproject/output.log',
    level=logging.INFO,
    format='%(asctime)s - %(message)s'
)

# Load the Iowa electricity dataset
source = data.iowa_electricity.url

# Define the base with temporal x-axis
base = alt.Chart(source).encode(
    x=alt.X('year(year):T', title='Year', scale=alt.Scale(type='time'))
)

# Layer 1: IQR error band
errorband = base.mark_errorband(
    extent='iqr',
    interpolate='monotone'
).encode(
    y=alt.Y('net_generation:Q', title='Net Generation')
)

# Layer 2: Median line
median_line = base.mark_line().encode(
    y=alt.Y('median(net_generation):Q')
)

# Layer 3: Horizontal dashed rule at y = 0
zero_rule = alt.Chart().mark_rule(
    strokeDash=[4, 4],
    color='red'
).encode(
    y=alt.Y(datum=0)
)

# Layer 4: Text annotation for the year with the largest median net_generation
# Precompute per-year median, then use window rank to pick the top year
annotation = alt.Chart(source).transform_aggregate(
    median_gen='median(net_generation)',
    groupby=['year(year)']
).transform_window(
    rank='rank()',
    sort=[alt.SortField('median_gen', order='descending')]
).transform_filter(
    alt.datum.rank == 1
).transform_calculate(
    label="year(datum['year(year)']) + ': ' + format(datum['median_gen'], ',.1f')"
).mark_text(
    align='left',
    baseline='bottom',
    dx=5,
    dy=-5,
    fontSize=12
).encode(
    x=alt.X('year(year):T', scale=alt.Scale(type='time')),
    y=alt.Y('median_gen:Q'),
    text=alt.Text('label:N')
)

# Combine all layers
chart = alt.layer(
    errorband,
    median_line,
    zero_rule,
    annotation
).properties(
    title=alt.TitleParams(
        text='Iowa Electricity Net Generation',
        subtitle='Yearly distribution across source categories with median trend'
    ),
    width=700,
    height=400
)

# Save the chart
output_path = '/home/user/myproject/chart.html'
chart.save(output_path)

logging.info(f'Chart written: {output_path}')
print(f'Chart written: {output_path}')