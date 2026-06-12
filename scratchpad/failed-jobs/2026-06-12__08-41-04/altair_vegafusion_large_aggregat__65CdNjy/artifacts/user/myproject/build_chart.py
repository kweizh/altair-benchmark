"""
build_chart.py
--------------
Generates a 60,000-row synthetic dataset and renders a 2D binned heatmap using
Vega-Altair with the VegaFusion data transformer to bypass the default 5,000-row
MaxRowsError limit.

Outputs:
  chart.html           – self-contained HTML file with the embedded chart
  transformed_data.csv – post-transform aggregated bin data extracted via
                         chart.transformed_data()
"""

import random
import pandas as pd
import altair as alt

# ── 1. Reproducible synthetic data ──────────────────────────────────────────
random.seed(42)

N = 60_000
x_vals = [random.randint(0, 99) for _ in range(N)]
y_vals = [random.randint(0, 49) for _ in range(N)]
z_vals = [random.random() for _ in range(N)]

df = pd.DataFrame({"x": x_vals, "y": y_vals, "z": z_vals})

# ── 2. Enable VegaFusion so large datasets don't raise MaxRowsError ──────────
alt.data_transformers.enable("vegafusion")

# ── 3. Build 2-D binned heatmap ──────────────────────────────────────────────
chart = (
    alt.Chart(df)
    .mark_rect()
    .encode(
        x=alt.X("x:Q", bin=alt.Bin(maxbins=20)),
        y=alt.Y("y:Q", bin=alt.Bin(maxbins=20)),
        color=alt.Color(
            "z:Q",
            aggregate="mean",
            scale=alt.Scale(scheme="magma"),
        ),
    )
    .properties(
        title="2-D Binned Heatmap (mean z)",
        width=500,
        height=400,
    )
)

# ── 4. Save self-contained HTML ──────────────────────────────────────────────
out_html = "/home/user/myproject/chart.html"
chart.save(out_html)
print(f"Chart saved → {out_html}")

# ── 5. Extract post-transform aggregated data and write CSV ──────────────────
agg_df = chart.transformed_data()
out_csv = "/home/user/myproject/transformed_data.csv"
agg_df.to_csv(out_csv, index=False)
print(f"Aggregated data saved → {out_csv}  ({len(agg_df)} rows)")

# ── 6. Quick sanity-check ────────────────────────────────────────────────────
assert len(agg_df) >= 50, (
    f"Expected at least 50 aggregated rows, got {len(agg_df)}"
)
print("All checks passed – exiting with code 0.")
