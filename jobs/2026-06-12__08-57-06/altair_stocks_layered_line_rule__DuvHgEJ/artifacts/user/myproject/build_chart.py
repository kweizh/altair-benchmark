import altair as alt
from vega_datasets import data

# Load the stocks data from URL with explicit types
source = data.stocks.url

# Build the layered chart
chart = alt.layer(
    # Layer 1: GOOG price line
    alt.Chart(source).mark_line().transform_filter(
        alt.datum.symbol == "GOOG"
    ).encode(
        x=alt.X("date:T", title="Date"),
        y=alt.Y("price:Q", title="Price"),
    ),
    # Layer 2: Red dashed horizontal rule at y=300
    alt.Chart().mark_rule(color="red", strokeDash=[4, 4]).encode(
        y=alt.datum(300),
    ),
    # Layer 3: Gray vertical rule at Oct 1, 2008
    alt.Chart().mark_rule(color="gray").encode(
        x=alt.datum(alt.DateTime(year=2008, month=10, day=1)),
    ),
    # Layer 4: "Crisis" text annotation at Oct 1, 2008
    alt.Chart().mark_text(
        text="Crisis",
        align="left",
        baseline="top",
        dx=5,
        dy=5,
    ).encode(
        x=alt.datum(alt.DateTime(year=2008, month=10, day=1)),
        y=alt.value(20),
        text=alt.value("Crisis"),
    ),
).properties(
    width=600,
    height=300,
)

# Save as self-contained HTML
chart.save("/home/user/myproject/chart.html")
print("Chart saved to /home/user/myproject/chart.html")
