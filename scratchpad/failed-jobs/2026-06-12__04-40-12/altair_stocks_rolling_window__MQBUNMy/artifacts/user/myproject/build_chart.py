import altair as alt
from vega_datasets import data

source = data.stocks.url

options = ['MSFT', 'AMZN', 'IBM', 'GOOG', 'AAPL']
symbol_dropdown = alt.binding_select(options=options, name='Symbol ')
symbol_select = alt.param(name='symbol_selection', bind=symbol_dropdown, value='MSFT')

base = alt.Chart(source).transform_filter(
    alt.datum.symbol == symbol_select
).add_params(
    symbol_select
)

raw_line = base.mark_line(opacity=0.3).encode(
    x='date:T',
    y='price:Q',
    color='symbol:N'
)

rolling_line = base.transform_window(
    rolling_mean='mean(price)',
    frame=[-15, 15],
    groupby=['symbol']
).mark_line(strokeWidth=2).encode(
    x='date:T',
    y='rolling_mean:Q',
    color='symbol:N'
)

rule = base.transform_joinaggregate(
    all_time_mean='mean(price)',
    groupby=['symbol']
).mark_rule(strokeDash=[4, 4]).encode(
    y='all_time_mean:Q',
    color='symbol:N'
)

chart = alt.layer(
    raw_line,
    rolling_line,
    rule
).interactive(bind_y=False)

chart.save('/home/user/myproject/chart.html')
