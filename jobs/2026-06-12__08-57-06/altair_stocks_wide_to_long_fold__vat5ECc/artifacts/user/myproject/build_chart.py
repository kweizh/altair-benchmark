import pandas as pd
import altair as alt

# ── 1. Construct wide-form DataFrame ──────────────────────────────────────────
# 12 monthly observations for AAPL, AMZN, GOOG
dates = pd.date_range("2025-01-01", periods=12, freq="MS")

# Plausible synthetic monthly prices (noise around a trend)
import numpy as np
np.random.seed(42)

aapl = np.round(np.cumsum(np.random.normal(0.5, 2, 12)) + 170, 2)
amzn = np.round(np.cumsum(np.random.normal(0.3, 3, 12)) + 145, 2)
goog = np.round(np.cumsum(np.random.normal(0.4, 2.5, 12)) + 135, 2)

df = pd.DataFrame(
    {
        "Date": dates,
        "AAPL": aapl,
        "AMZN": amzn,
        "GOOG": goog,
    }
)

# ── 2. Build the Altair chart with transform_fold ────────────────────────────
chart = (
    alt.Chart(df)
    .transform_fold(
        fold=["AAPL", "AMZN", "GOOG"],
        as_=["company", "price"],
    )
    .mark_line()
    .encode(
        x=alt.X("Date:T", title="Date"),
        y=alt.Y("price:Q", title="Price (USD)"),
        color=alt.Color("company:N", title="Company"),
    )
    .properties(
        title="Monthly Stock Prices (Wide-to-Long via transform_fold)",
        width=600,
        height=400,
    )
)

# ── 3. Save as self-contained HTML ───────────────────────────────────────────
chart.save("/home/user/myproject/chart.html")
print("Chart saved to /home/user/myproject/chart.html")
