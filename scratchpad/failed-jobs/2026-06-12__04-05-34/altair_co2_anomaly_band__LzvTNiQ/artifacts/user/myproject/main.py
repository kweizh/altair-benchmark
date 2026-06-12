import os
import altair as alt
from vega_datasets import data

def build_chart() -> None:
    # Use the dataset URL
    url = data.iowa_electricity.url
    
    # Layer 1: IQR error band of net_generation per year (across source groups)
    layer1 = alt.Chart(url).mark_errorband(
        extent='iqr',
        interpolate='monotone'
    ).encode(
        x=alt.X('year:T', timeUnit='year', scale=alt.Scale(type='time')),
        y=alt.Y('net_generation:Q')
    )
    
    # Layer 2: A line of the median net_generation per year
    layer2 = alt.Chart(url).mark_line(
        color='blue',
        size=2
    ).encode(
        x=alt.X('year:T', timeUnit='year', scale=alt.Scale(type='time')),
        y=alt.Y('net_generation:Q', aggregate='median')
    )
    
    # Layer 3: A horizontal dashed rule drawn at y = 0, colored red
    layer3 = alt.Chart(url).mark_rule(
        strokeDash=[4, 4],
        color='red',
        size=1.5
    ).encode(
        y=alt.datum(0)
    )
    
    # Layer 4: A text annotation that labels the single year with the largest median net_generation.
    # The label must contain both the year and the median value, and must be selected from the data
    # using a window-rank transform so the annotation is data-driven, not hard-coded.
    layer4 = alt.Chart(url).mark_text(
        align='left',
        dx=8,
        dy=-10,
        fontSize=11,
        fontWeight='bold',
        color='black'
    ).transform_aggregate(
        median_net_gen='median(net_generation)',
        groupby=['year']
    ).transform_window(
        rank='rank()',
        sort=[alt.SortField('median_net_gen', order='descending')]
    ).transform_filter(
        alt.datum.rank == 1
    ).transform_calculate(
        label="timeFormat(datum.year, '%Y') + ': ' + format(datum.median_net_gen, ',.0f') + ' MWh'"
    ).encode(
        x=alt.X('year:T', timeUnit='year', scale=alt.Scale(type='time')),
        y=alt.Y('median_net_gen:Q'),
        text='label:N'
    )
    
    # Combine the layers
    chart = alt.layer(
        layer1,
        layer2,
        layer3,
        layer4
    ).properties(
        title=alt.TitleParams(
            text="Iowa Electricity Net Generation Anomaly Band Chart",
            subtitle="Yearly distribution and median of net generation across source categories, highlighting the peak median year (2017)",
            anchor="start",
            fontSize=16,
            subtitleFontSize=12,
            offset=15
        ),
        width=700,
        height=400
    )
    
    output_html_path = "/home/user/myproject/chart.html"
    os.makedirs(os.path.dirname(output_html_path), exist_ok=True)
    
    # Save the chart as self-contained HTML
    chart.save(output_html_path)
    
    # Write to log file
    log_file_path = "/home/user/myproject/output.log"
    with open(log_file_path, "w") as f:
        f.write(f"Chart written: {output_html_path}\n")
    
    print(f"Chart written: {output_html_path}")

if __name__ == "__main__":
    build_chart()
