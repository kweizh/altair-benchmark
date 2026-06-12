import altair as alt
from vega_datasets import data

source = data.stocks.url

line = alt.Chart().mark_line().encode(
    x='date:T',
    y='price:Q'
)

rule_y = alt.Chart().mark_rule(color='red', strokeDash=[4, 4]).encode(
    y=alt.datum(300)
)

rule_x = alt.Chart().mark_rule(color='gray').encode(
    x=alt.datum(alt.DateTime(year=2008, month=10, day=1))
)

text = alt.Chart().mark_text(align='left', dx=5, dy=-100).encode(
    x=alt.datum(alt.DateTime(year=2008, month=10, day=1)),
    y=alt.datum(300),
    text=alt.datum('Crisis')
)

chart = alt.layer(line, rule_y, rule_x, text, data=source).transform_filter(
    alt.datum.symbol == 'GOOG'
).properties(
    width=600,
    height=300
)

chart.save('/home/user/myproject/chart.html')
