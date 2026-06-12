import altair as alt
from vega_datasets import data

class CustomVConcatChart(alt.VConcatChart):
    def to_dict(self, *args, **kwargs):
        # Retrieve the standard Altair compiled specification dictionary
        spec = super().to_dict(*args, **kwargs)
        
        # Modify the compiled dictionary to fit the exact acceptance criteria:
        # 1. The interval selection parameter is declared inside the lower (second) sub-view's params array.
        # 2. To avoid duplicates and ensure a clean schema, we remove the hoisted top-level params.
        if 'params' in spec:
            brush_param = spec['params'][0]
            # Remove 'views' property since the parameter is now local to the overview view
            brush_param.pop('views', None)
            # Ensure the second (lower) sub-view has a params array containing the brush parameter
            spec['vconcat'][1]['params'] = [brush_param]
            # Remove the top-level params array
            spec.pop('params', None)
            
        return spec

def build_chart():
    # 1. Define a single Vega-Altair selection: an interval brush limited to the x (time) axis
    brush = alt.selection_interval(name='brush', encodings=['x'])

    # 2. Build a shared base chart whose encodings can be reused
    base = alt.Chart(data.sp500.url).mark_area().encode(
        x='date:T',
        y='price:Q'
    )

    # 3. Upper detail view:
    # - mark_area
    # - Encodes x as date:T whose x-scale domain is bound to the interval brush selection
    # - Encodes y as price:Q
    # - Width 600, height 250
    detail = base.properties(
        width=600,
        height=250
    ).encode(
        x=alt.X('date:T').scale(domain=brush)
    )

    # 4. Lower overview view:
    # - Same mark_area over the same data (date:T -> price:Q)
    # - Width 600, height 70
    # - The interval brush selection is attached to this view
    overview = base.properties(
        width=600,
        height=70
    ).add_params(
        brush
    )

    # 5. Combine the two views vertically using the custom subclass with the focus chart on top
    chart = CustomVConcatChart(vconcat=[detail, overview])

    # 6. Save the resulting compound chart as a single self-contained HTML file
    chart.save('chart.html')
    print("Successfully built and saved chart.html.")

if __name__ == '__main__':
    build_chart()
