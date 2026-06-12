import altair as alt
from vega_datasets import data
import os

iris = data.iris()

base = alt.Chart(iris).encode(
    x='petalLength:Q',
    y='petalWidth:Q',
    color='species:N'
)

# Layer A - Raw points
points = base.mark_point()

# Layer B - Parametric regression line per species
regression = base.transform_regression(
    'petalLength', 'petalWidth', groupby=['species']
).mark_line()

# Layer C - LOESS smoothed line per species
loess = base.transform_loess(
    'petalLength', 'petalWidth', groupby=['species'], bandwidth=0.6
).mark_line(strokeDash=[4, 4])

# Layer D - 95% confidence band per species
band = base.mark_errorband(extent='ci')

# Combine layers
chart = alt.layer(
    band, points, regression, loess
).properties(
    title=alt.Title(
        text="Iris Petal Length vs Width",
        subtitle=["Regression, LOESS, and Confidence Band", "Grouped by species"]
    )
)

# Save the charts
chart.save('/home/user/iris_chart/chart.json')
chart.save('/home/user/iris_chart/chart.html')

with open('/home/user/iris_chart/output.log', 'w') as f:
    f.write('Chart saved: /home/user/iris_chart/chart.html\n')
