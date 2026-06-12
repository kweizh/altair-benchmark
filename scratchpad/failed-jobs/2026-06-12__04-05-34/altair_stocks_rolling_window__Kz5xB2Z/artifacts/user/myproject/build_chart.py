import os
import altair as alt
from vega_datasets import data

def build_chart():
    # 1. Define the dropdown selection
    # The dropdown options must be exactly the five tickers in the stocks dataset: MSFT, AMZN, IBM, GOOG, AAPL
    dropdown_options = ['MSFT', 'AMZN', 'IBM', 'GOOG', 'AAPL']
    dropdown = alt.binding_select(
        options=dropdown_options, 
        name='Select Symbol: '
    )
    
    symbol_param = alt.param(
        name='symbol_selection',
        value='MSFT',
        bind=dropdown
    )
    
    # 2. Define the base chart with the filter transform
    # The data source is the well-known data.stocks.url dataset
    base = alt.Chart(data.stocks.url).transform_filter(
        alt.datum.symbol == symbol_param
    ).properties(
        width=800,
        height=400,
        title="Stock Price Analysis: Raw, 30-Day Rolling Mean, and All-Time Mean"
    )
    
    # Layer 1: A thin raw price line per symbol (low opacity), with price:Q on y and color by symbol:N.
    raw_line = base.mark_line(
        opacity=0.3, 
        size=1
    ).encode(
        x=alt.X('date:T', title='Date'),
        y=alt.Y('price:Q', title='Stock Price ($)'),
        color=alt.Color('symbol:N', title='Symbol')
    )
    
    # Layer 2: A bold rolling-mean line per symbol, where the rolling mean is computed inside the spec 
    # with a window transform that averages price over a 30-trading-day centered window (15 days before and 15 days after each point), grouped by symbol.
    rolling_line = base.mark_line(
        size=3
    ).transform_window(
        rolling_mean='mean(price)',
        frame=[-15, 15],
        groupby=['symbol']
    ).encode(
        x='date:T',
        y='rolling_mean:Q',
        color='symbol:N'
    )
    
    # Layer 3: A horizontal dashed reference rule per symbol at the symbol's all-time mean price. 
    # The all-time mean must be computed inside the spec with a join-aggregate transform grouped by symbol.
    ref_rule = base.mark_rule(
        strokeDash=[4, 4]
    ).transform_joinaggregate(
        all_time_mean='mean(price)',
        groupby=['symbol']
    ).encode(
        y='all_time_mean:Q',
        color='symbol:N'
    )
    
    # Combine layers, add params, and enable pan/zoom on the x-axis (bind_y=False restricts it to x-axis)
    chart = alt.layer(
        raw_line, 
        rolling_line, 
        ref_rule
    ).add_params(
        symbol_param
    ).interactive(
        bind_y=False
    )
    
    # Ensure output directory exists
    os.makedirs('/home/user/myproject', exist_ok=True)
    
    # Save the chart to /home/user/myproject/chart.html
    output_path = '/home/user/myproject/chart.html'
    chart.save(output_path)
    print(f"Chart saved successfully to {output_path}")

if __name__ == "__main__":
    build_chart()
