import altair as alt
from vega_datasets import data

source = data.seattle_weather.url

base = alt.Chart(source).transform_calculate(
    temp_mean="(datum.temp_max + datum.temp_min) / 2",
    tooltip_text="datum.weather + ' on ' + datum.date + ' | Mean Temp: ' + datum.temp_mean + ' | Precip: ' + datum.precipitation"
)

area = base.mark_area(color='#ffcc99', opacity=0.5).encode(
    x=alt.X('date:T', title='Date'),
    y=alt.Y('temp_max:Q', title='Temperature (°C)'),
    y2=alt.Y2('temp_min:Q')
)

line = base.mark_line(color='red').encode(
    x='date:T',
    y='temp_mean:Q'
)

bar = base.mark_bar(color='#6699ff', opacity=0.5).encode(
    x='date:T',
    y=alt.Y('precipitation:Q', title='Precipitation (mm)')
)

rule0 = alt.Chart(source).mark_rule(strokeDash=[4, 4], color='black').encode(
    y=alt.datum(0)
)

hover = alt.selection_point(
    encodings=['x'],
    nearest=True,
    on='pointerover',
    empty=False
)

points = base.mark_point(size=0).encode(
    x='date:T',
    y='temp_mean:Q'
).add_params(hover)

vrule = base.mark_rule(color='gray').encode(
    x='date:T',
    opacity=alt.condition(hover, alt.value(1), alt.value(0))
)

text = base.mark_text(align='left', dx=5, dy=-15).encode(
    x='date:T',
    y='temp_mean:Q',
    text=alt.condition(hover, 'tooltip_text:N', alt.value(''))
)

temp_layers = alt.layer(area, line, rule0, points, vrule, text)
chart = alt.layer(bar, temp_layers).resolve_scale(y='independent').properties(
    width=800,
    height=400,
    title='Seattle Weather: Temperature Range, Mean, and Precipitation'
)

chart.save('/home/user/myproject/chart.html')
