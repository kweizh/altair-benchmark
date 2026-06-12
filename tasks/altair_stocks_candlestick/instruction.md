# Interactive Candlestick + Volume Chart with Vega-Altair

## Background
You are visualizing daily stock activity for a single ticker. A synthetic OHLCV dataset is already provided in the project directory as `ohlcv.csv` (columns: `date`, `open`, `high`, `low`, `close`, `volume`). Your task is to build an interactive, financially conventional candlestick visualization paired with a volume overview, all expressed declaratively with Vega-Altair.

## Requirements
- Read the OHLCV dataset from `ohlcv.csv`.
- Produce a vertically composed (vconcat) chart consisting of two views that share the `date` axis:
  - **Upper view (candlestick)**: a layered chart combining a high–low wick and an open–close body for each trading day. The body fill must be encoded by a per-row predicate comparing `open` and `close` so that up days (close ≥ open) and down days (close < open) get distinct colors.
  - **Lower view (volume)**: a bar chart of `volume` over `date`.
- The lower view must host an interval brush that is constrained to the `x` (date) encoding only. The upper view's x-axis domain must be bound to that brush so that brushing on the lower chart zooms / pans the candlestick chart.
- Save the chart as both a self-contained HTML file and a Vega-Lite JSON spec file.

## Implementation Hints
- Use a single Altair `Chart` base for the candlestick view and overlay a `mark_rule` (low–high wick) with a `mark_bar` (open–close body) via layering. The wick uses `y` / `y2` of `low` / `high`; the body uses `y` / `y2` of `open` / `close`.
- Encode the bullish/bearish coloring with a conditional value definition driven by a predicate on `datum.open` and `datum.close` (e.g. `alt.condition` or `alt.when`), choosing a green for up days and a red for down days.
- Define an `alt.selection_interval(encodings=['x'])` parameter, attach it to the lower volume chart with `add_params`, and reference it from the upper chart's x scale `domain` so brushing controls the focus.
- Compose the two charts with vertical concatenation (`&` / `alt.vconcat`).
- Persist the chart via `chart.save('chart.html')` and `chart.save('chart.json')` (or equivalent) so both artifacts exist on disk.

## Acceptance Criteria
- Project path: /home/user/altair_stocks_candlestick
- Command: python3 build_chart.py
- The command, when executed inside the project directory, must read `ohlcv.csv` and (over)write the following two files in the same directory:
  - `chart.html` — a standalone HTML file embedding the Vega-Lite spec via vega-embed.
  - `chart.json` — the Vega-Lite JSON specification of the composed chart.
- The Vega-Lite spec in `chart.json` must satisfy:
  - The top level is a `vconcat` specification with exactly two child views (upper then lower).
  - The upper view is a `layer` containing a `rule` mark and a `bar` mark.
    - The `rule` layer encodes `y` from `low` and `y2` from `high`.
    - The `bar` layer encodes `y` from `open` and `y2` from `close`.
    - At least one of these two layers uses a `color` encoding whose `condition` references both `open` and `close` (e.g. `datum.open <= datum.close`).
  - The lower view uses a `bar` mark with `y` encoded from `volume` and `x` encoded from `date` (temporal).
  - There is an interval selection parameter (`select.type == 'interval'`) whose `encodings` is exactly `['x']`. The selection is attached to the lower view (it appears in the lower view's `params`).
  - The upper view's x channel scale `domain` references the interval selection parameter by name.
- Browser verification: When `chart.html` is loaded in a headless browser, the rendered SVG/Canvas must show both a candlestick layer (vertical wick + body) in the upper region and bars in the lower region.

