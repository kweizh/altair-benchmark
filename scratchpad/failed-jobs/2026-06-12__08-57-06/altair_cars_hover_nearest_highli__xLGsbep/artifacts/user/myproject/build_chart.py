import altair as alt
from vega_datasets import data

# ── shared base chart with URL-based data source & explicit types ──────────
base = alt.Chart(data.cars.url).encode(
    alt.X("Horsepower:Q", scale=alt.Scale(zero=False)),
    alt.Y("Miles_per_Gallon:Q", scale=alt.Scale(zero=False)),
)

# ── hover selection ─────────────────────────────────────────────────────────
hover = alt.selection_point(
    on="pointerover",
    nearest=True,
    empty=False,
)

# ── point layer ─────────────────────────────────────────────────────────────
points = (
    base.mark_point()
    .add_params(hover)
    .encode(
        color=alt.condition(hover, "Origin:N", alt.value("lightgray")),
    )
)

# ── text label layer ────────────────────────────────────────────────────────
labels = base.mark_text(dy=-10).encode(
    text="Name:N",
    opacity=alt.condition(hover, alt.value(1), alt.value(0)),
)

# ── combine layers & set dimensions ─────────────────────────────────────────
chart = alt.layer(points, labels).properties(
    width=600,
    height=400,
)

# ── save to self-contained HTML ─────────────────────────────────────────────
chart.save("/home/user/myproject/chart.html")
print("chart.html written successfully")
