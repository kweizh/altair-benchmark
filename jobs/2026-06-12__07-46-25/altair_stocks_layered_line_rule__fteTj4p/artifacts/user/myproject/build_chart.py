import altair as alt
from vega_datasets import data

def build_chart():
    # Use URL-based data source
    source = data.stocks.url

    # Layer 1: Line mark of price over date for GOOG
    line = alt.Chart(source).mark_line().encode(
        x='date:T',
        y='price:Q'
    ).transform_filter(
        alt.datum.symbol == 'GOOG'
    )

    # Layer 2: Red horizontal rule at y = 300, strokeDash [4, 4]
    rule_y = alt.Chart().mark_rule(
        color='red',
        strokeDash=[4, 4]
    ).encode(
        y=alt.datum(300)
    )

    # Layer 3: Gray vertical rule at October 1, 2008
    rule_x = alt.Chart().mark_rule(
        color='gray'
    ).encode(
        x=alt.datum(alt.DateTime(year=2008, month=10, day=1))
    )

    # Layer 4: Text annotation positioned at the same crisis date
    text = alt.Chart().mark_text(
        align='left',
        dx=5,
        dy=-100,
        fontSize=12,
        fontWeight='bold'
    ).encode(
        x=alt.datum(alt.DateTime(year=2008, month=10, day=1)),
        y=alt.datum(350),
        text=alt.value('Crisis')
    )

    # Compose the layered chart
    chart = alt.layer(
        line,
        rule_y,
        rule_x,
        text
    ).properties(
        width=600,
        height=300
    )

    # Save to HTML
    chart.save('/home/user/myproject/chart.html')
    print("Chart saved successfully to /home/user/myproject/chart.html")

if __name__ == '__main__':
    build_chart()
