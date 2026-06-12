import altair as alt
from vega_datasets import data

# Use URL-based data source
source = data.stocks.url

# Layer 1: GOOG stock price line
line = (
    alt.Chart(source)
    .mark_line()
    .encode(
        x="date:T",
        y="price:Q",
        color=alt.value("steelblue"),
    )
    .transform_filter(alt.datum.symbol == "GOOG")
)

# Layer 2: Red dashed horizontal rule at price = 300 (threshold annotation)
threshold_rule = (
    alt.Chart(source)
    .mark_rule(strokeDash=[4, 4], color="red")
    .encode(
        y=alt.datum(300),
    )
)

# Layer 3: Gray vertical rule at October 1, 2008 (crisis date)
crisis_date = alt.DateTime(year=2008, month=10, day=1)

crisis_rule = (
    alt.Chart(source)
    .mark_rule(color="gray")
    .encode(
        x=alt.datum(crisis_date),
    )
)

# Layer 4: "Crisis" text annotation at the crisis date
crisis_text = (
    alt.Chart(source)
    .mark_text(dx=10, align="left", baseline="middle", fontSize=12, fontWeight="bold")
    .encode(
        x=alt.datum(crisis_date),
        y=alt.value(50),
        text=alt.value("Crisis"),
    )
)

# Compose the layered chart
chart = alt.layer(line, threshold_rule, crisis_rule, crisis_text).properties(
    width=600,
    height=300,
)

# Save to HTML
chart.save("/home/user/myproject/chart.html")
print("Chart saved to /home/user/myproject/chart.html")