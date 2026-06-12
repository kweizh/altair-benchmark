import altair as alt
from vega_datasets import data

cars = data.cars()

# Single shared legend-bound selection over Origin
legend_sel = alt.selection_point(fields=["Origin"], bind="legend")

opacity_cond = alt.condition(legend_sel, alt.value(1), alt.value(0.15))

# View A — Scatter plot
scatter = (
    alt.Chart(cars)
    .mark_point()
    .encode(
        x=alt.X("Horsepower:Q"),
        y=alt.Y("Miles_per_Gallon:Q"),
        color=alt.Color("Origin:N"),
        opacity=opacity_cond,
    )
)

# View B — Stacked bar chart (no xOffset → stacked by default)
stacked_bar = (
    alt.Chart(cars)
    .mark_bar()
    .encode(
        x=alt.X("Cylinders:O"),
        y=alt.Y("count():Q"),
        color=alt.Color("Origin:N"),
        opacity=opacity_cond,
    )
)

# View C — Histogram of Acceleration
histogram = (
    alt.Chart(cars)
    .mark_bar()
    .encode(
        x=alt.X("Acceleration:Q", bin=True),
        y=alt.Y("count():Q"),
        color=alt.Color("Origin:N"),
        opacity=opacity_cond,
    )
)

# Compose: (A | B) & C  →  vconcat( hconcat(A, B), C )
chart = ((scatter | stacked_bar) & histogram).add_params(legend_sel)

chart.save("/home/user/myproject/chart.html")
print("Saved chart.html")
