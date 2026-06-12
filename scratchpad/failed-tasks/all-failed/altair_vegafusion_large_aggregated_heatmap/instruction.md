# Large Aggregated Heatmap with VegaFusion in Vega-Altair

## Background
Vega-Altair refuses to render datasets with more than 5,000 rows by default (`MaxRowsError`). Build an Altair workflow that processes a 60,000-row synthetic dataset by enabling the VegaFusion data transformer, produces a 2D binned heatmap saved as a self-contained HTML file, and also exports the post-transform aggregated rows as a CSV file via `chart.transformed_data()`.

## Requirements
- Implement the build script as `/home/user/myproject/build_chart.py`.
- Generate a deterministic synthetic pandas DataFrame with 60,000 rows and three columns:
  - `x`: uniform random integers in `[0, 99]` (inclusive).
  - `y`: uniform random integers in `[0, 49]` (inclusive).
  - `z`: uniform random floats in `[0.0, 1.0)`.
  - Use `random.seed(42)` from Python's standard `random` module to seed the data generation so the dataset is reproducible.
- Enable the VegaFusion data transformer with `alt.data_transformers.enable('vegafusion')` so the chart does **not** raise `altair.MaxRowsError`.
- Build a single 2D binned heatmap chart using `mark_rect()` that encodes:
  - `x` on the X axis as a quantitative field with `bin(maxbins=20)`.
  - `y` on the Y axis as a quantitative field with `bin(maxbins=20)`.
  - color as the `mean` aggregate of `z`, with a continuous color scale using the `'magma'` color scheme.
- Save the chart as `/home/user/myproject/chart.html`.
- Use `chart.transformed_data()` to extract the post-transform aggregated DataFrame produced by Vega-Lite (one row per non-empty bin) and write it to `/home/user/myproject/transformed_data.csv` as a valid CSV file. The CSV must contain at least 50 rows of aggregated bin data (excluding the header).
- The script must exit with code 0 and must not raise or print any `MaxRowsError` text.

## Implementation Hints
- Generate the data with Python's built-in `random` module so that `random.seed(42)` deterministically controls every value of `x`, `y`, and `z`. Use `random.randint(0, 99)` for `x`, `random.randint(0, 49)` for `y`, and `random.random()` for `z`.
- VegaFusion exposes both a `'vegafusion'` data transformer and the backend for `chart.transformed_data()`. Install it via `pip install "vegafusion[embed]"` plus `vegafusion-python-embed`.
- Enable VegaFusion globally **before** building the chart (`alt.data_transformers.enable('vegafusion')`).
- For the heatmap, use `alt.X('x:Q', bin=alt.Bin(maxbins=20))`, `alt.Y('y:Q', bin=alt.Bin(maxbins=20))`, and `alt.Color('z:Q', aggregate='mean', scale=alt.Scale(scheme='magma'))` (or equivalent syntax).
- `chart.transformed_data()` returns a single pandas DataFrame for a unit chart. Use `df.to_csv('/home/user/myproject/transformed_data.csv', index=False)` to write it.
- See the official Altair docs section on large datasets (https://altair-viz.github.io/user_guide/large_datasets.html) and the VegaFusion site (https://vegafusion.io/) for details on enabling VegaFusion and accessing transformed data.

## Acceptance Criteria
- Project path: /home/user/myproject
- Command: python3 build_chart.py
- The command must exit with code 0 and must not raise `altair.MaxRowsError` (no `MaxRowsError` text in stderr).
- The build script `/home/user/myproject/build_chart.py` must call `alt.data_transformers.enable('vegafusion')`.
- The command must produce `/home/user/myproject/chart.html`, which must be a non-empty file containing a renderable Vega/Vega-Lite specification embedded in the HTML.
- The command must produce `/home/user/myproject/transformed_data.csv`, which must be a valid CSV with a header row and at least 50 data rows.
- The embedded chart specification (whether Vega-Lite or compiled Vega) must encode a `rect`-mark heatmap with:
  - Binned X channel with `maxbins == 20`.
  - Binned Y channel with `maxbins == 20`.
  - Color channel aggregating `mean(z)` with a continuous scheme named `'magma'`.
- Browser verification: Loading `chart.html` in a browser must render the chart without JavaScript console errors; the rendered output must include a visible rectangular heatmap grid and a continuous color legend using the magma color ramp.

