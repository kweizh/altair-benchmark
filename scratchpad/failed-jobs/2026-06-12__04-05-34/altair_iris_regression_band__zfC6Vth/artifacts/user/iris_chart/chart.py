import os
import altair as alt
from vega_datasets import data

def main():
    # Load the classic Iris dataset
    iris = data.iris()

    # Define the base chart with shared x, y, and color encodings
    base = alt.Chart(iris).encode(
        x=alt.X('petalLength:Q', title='Petal Length'),
        y=alt.Y('petalWidth:Q', title='Petal Width'),
        color=alt.Color('species:N', title='Species')
    )

    # 1. Layer D — 95% confidence band per species (placed at the bottom)
    band = base.mark_errorband(extent='ci')

    # 2. Layer B — Parametric regression line per species
    regression = base.transform_regression(
        'petalLength', 'petalWidth', groupby=['species']
    ).mark_line()

    # 3. Layer C — LOESS smoothed line per species (dashed)
    loess = base.transform_loess(
        'petalLength', 'petalWidth', groupby=['species'], bandwidth=0.6
    ).mark_line(strokeDash=[4, 4])

    # 4. Layer A — Raw points (on top)
    points = base.mark_point()

    # Combine the four layers
    chart = alt.layer(band, regression, loess, points).properties(
        title=alt.Title(
            text="Iris Dataset: Petal Length vs Petal Width",
            subtitle=[
                "Comparison of Parametric Regression and LOESS Smoothing (bandwidth=0.6)",
                "with 95% Confidence Intervals per Species"
            ]
        )
    ).interactive()

    # Define output paths
    base_dir = "/home/user/iris_chart"
    os.makedirs(base_dir, exist_ok=True)
    
    json_path = os.path.join(base_dir, "chart.json")
    html_path = os.path.join(base_dir, "chart.html")
    log_path = os.path.join(base_dir, "output.log")

    # Save the chart
    chart.save(json_path)
    chart.save(html_path)

    # Write output log
    with open(log_path, "w") as f:
        f.write(f"Chart saved: {html_path}\n")

    print(f"Chart successfully saved to {json_path} and {html_path}")

if __name__ == "__main__":
    main()
