import altair as alt
from vega_datasets import data

# URL-based data source — types must be declared explicitly via shorthand
source = data.cars.url

# Shared base chart
base = alt.Chart(source).encode(
    x=alt.X("Horsepower:Q", scale=alt.Scale(zero=False)),
    y=alt.Y("Miles_per_Gallon:Q", scale=alt.Scale(zero=False)),
)

# Hover selection: nearest point under the pointer
hover = alt.selection_point(
    on="pointerover",
    nearest=True,
    empty=False,
)

# ── Layer 1: scatter points ──────────────────────────────────────────────────
# Color is conditional: active hover → Origin color; otherwise lightgray
points = (
    base.mark_point()
    .encode(
        color=alt.condition(
            hover,
            alt.Color("Origin:N"),
            alt.value("lightgray"),
        )
    )
    .add_params(hover)
)

# ── Layer 2: text labels ─────────────────────────────────────────────────────
# Opacity is conditional: 1 on hover, 0 otherwise — label floats above point
labels = base.mark_text(dy=-10).encode(
    text=alt.Text("Name:N"),
    opacity=alt.condition(
        hover,
        alt.value(1),
        alt.value(0),
    ),
)

# ── Compose & export ─────────────────────────────────────────────────────────
chart = (
    alt.layer(points, labels)
    .properties(width=600, height=400)
)

chart.save("/home/user/myproject/chart.html")
print("Saved → /home/user/myproject/chart.html")
