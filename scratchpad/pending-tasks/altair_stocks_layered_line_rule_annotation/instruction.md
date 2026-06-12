# Layered Stock Price Chart with Crisis Annotations using Vega-Altair

## Background
Build a Vega-Altair layered visualization of the GOOG stock price over time, with annotation overlays highlighting a notional price threshold and a key historical event (the October 2008 financial crisis). The chart must be exported to a static HTML file that renders cleanly in a browser.

## Requirements
- Use `data.stocks.url` from `vega_datasets` as the data source (URL-based; declare types explicitly).
- Filter the data so only rows with `symbol == "GOOG"` are plotted.
- Compose a single layered chart with **at least 4 layers**:
  1. A `mark_line()` of `price` over `date` for GOOG.
  2. A **red** horizontal `mark_rule()` at the constant data value `y = 300`, with `strokeDash` `[4, 4]` (a dashed threshold annotation).
  3. A **gray** vertical `mark_rule()` at the constant date `October 1, 2008` (the crisis date).
  4. A `mark_text()` annotation positioned at the same crisis date that renders the literal label `"Crisis"`.
- Configure the chart with `width=600` and `height=300`.
- Save the resulting chart as a single self-contained HTML file using `chart.save(...)`.

## Implementation Hints
- For URL-based data sources, you must declare types in shorthand encodings (e.g., `date:T`, `price:Q`, `symbol:N`).
- Use `transform_filter` to restrict the data to GOOG before drawing the line.
- Use `alt.datum(300)` to encode a constant y-value for the horizontal threshold rule.
- Use `alt.datum(alt.DateTime(year=2008, month=10, day=1))` to encode a constant date for the vertical rule and the text annotation.
- Layers can be composed using `alt.layer(...)` or the `+` operator.
- Configure the text mark with reasonable typographic properties (for example a non-zero `dx` offset or `align`/`baseline`) so it doesn't overlap the vertical rule.

## Acceptance Criteria
- Project path: /home/user/myproject
- Command: python3 build_chart.py
- The command must produce `/home/user/myproject/chart.html` containing a renderable Vega-Lite specification.
- The embedded Vega-Lite specification must:
  - Be a layered chart with a top-level `layer` array of length >= 4.
  - Contain at least one `line` mark, two `rule` marks, and one `text` mark across the layers.
  - Include a `transform` of type `filter` whose expression references `symbol` and the value `"GOOG"`.
  - Have one `rule` layer whose `encoding.y.datum == 300`, whose mark has `strokeDash` equal to `[4, 4]`, and whose color is red.
  - Have a second `rule` layer whose `encoding.x.datum` is a `DateTime` object with `year == 2008` and `month == 10`.
  - Have a `text` layer whose `encoding.text` resolves to the literal value `"Crisis"`.
  - Have top-level `width == 600` and `height == 300`.
- Browser verification: Loading `chart.html` in a browser must render the GOOG line, the dashed red horizontal threshold rule, the vertical crisis rule, and the `"Crisis"` text label, with no JavaScript console errors.

