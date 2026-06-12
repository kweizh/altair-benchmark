import altair as alt
from vega_datasets import data

# URL-based data source — types must be declared explicitly in shorthand encodings
source = data.stocks.url

# --- Layer 1: GOOG price line ---
line = (
    alt.Chart(source)
    .transform_filter("datum.symbol === 'GOOG'")
    .mark_line()
    .encode(
        x="date:T",
        y="price:Q",
    )
)

# --- Layer 2: Horizontal dashed red threshold rule at price = 300 ---
h_rule = (
    alt.Chart()
    .mark_rule(color="red", strokeDash=[4, 4])
    .encode(
        y=alt.Y(datum=300),
    )
)

# --- Layer 3: Vertical gray crisis rule at October 1, 2008 ---
crisis_date = alt.DateTime(year=2008, month=10, day=1)

v_rule = (
    alt.Chart()
    .mark_rule(color="gray")
    .encode(
        x=alt.X(datum=crisis_date),
    )
)

# --- Layer 4: "Crisis" text annotation at the same date ---
crisis_text = (
    alt.Chart()
    .mark_text(
        align="left",
        baseline="top",
        dx=4,
        dy=4,
        color="gray",
        fontSize=12,
    )
    .encode(
        x=alt.X(datum=crisis_date),
        text=alt.value("Crisis"),
    )
)

# Compose all four layers and set chart dimensions
chart = alt.layer(line, h_rule, v_rule, crisis_text).properties(
    width=600,
    height=300,
    title="GOOG Stock Price with Crisis Annotation",
)

# Export as a self-contained HTML file
chart.save("chart.html")
print("chart.html written successfully.")
