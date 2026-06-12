# Slider-Driven Threshold Highlight with Vega-Altair

## Background
Build an interactive Vega-Altair scatter plot of the classic `cars` dataset where a horizontal slider widget controls a horsepower threshold. Points whose horsepower is below the threshold must be highlighted in one color, and points whose horsepower is at or above the threshold must use a second color. The chart must be exported as a self-contained HTML file that loads in a browser and responds live to slider movements.

## Requirements
- Use `data.cars.url` from `vega_datasets` as the data source (URL-based source; declare types explicitly).
- Render a scatter `mark_point` of `Horsepower` (x) vs. `Miles_per_Gallon` (y).
- Bind a range slider input to a top-level parameter that represents the live horsepower threshold:
  - Slider input: min `50`, max `250`, step `10`, name label exactly `"HP threshold: "`.
  - Parameter initial value: `150`.
- The point color must be a conditional value encoding driven by the slider parameter:
  - When `datum.Horsepower < <param>`: color value `"steelblue"`.
  - Otherwise: color value `"orange"`.
- Set the chart title to exactly `"MPG vs Horsepower (threshold)"`.
- Save the resulting chart as a single self-contained HTML file using `chart.save(...)`.

## Implementation Hints
- Use `alt.binding_range(...)` to build the slider input and `alt.param(value=..., bind=...)` to expose the live threshold as a top-level parameter.
- Drive the color encoding with `alt.when(<predicate>).then(alt.value('steelblue')).otherwise(alt.value('orange'))`, where the predicate compares `alt.datum.Horsepower` to the parameter object.
- Remember to attach the parameter to the chart via `add_params(...)` so the slider widget actually renders.
- Because the data source is the URL `data.cars.url`, declare field types explicitly in the encoding shorthands (e.g. `Horsepower:Q`, `Miles_per_Gallon:Q`).
- Use `properties(title=...)` to set the chart title.

## Acceptance Criteria
- Project path: /home/user/myproject
- Command: python3 build_chart.py
- The command must produce `/home/user/myproject/chart.html` containing a renderable Vega-Lite specification.
- The embedded Vega-Lite specification must:
  - Have a single mark of type `point`.
  - Declare exactly one parameter whose `bind` is a range input with `input == 'range'`, `min == 50`, `max == 250`, `step == 10`, `name == 'HP threshold: '`, and whose top-level `value == 150`.
  - Encode `x.field == 'Horsepower'` and `y.field == 'Miles_per_Gallon'`.
  - Have a `color` encoding that is a conditional value encoding whose test expression references the parameter name, `datum.Horsepower`, and the `<` operator; the `condition.value` must be `"steelblue"` and the otherwise `value` must be `"orange"`.
  - Have a top-level `title` equal to `"MPG vs Horsepower (threshold)"`.
- Browser verification: Loading `chart.html` in a browser must render the chart without JavaScript console errors. The page must display a slider labelled `"HP threshold: "` (initial value `150`); points with horsepower below the threshold must be colored steelblue and points at or above the threshold must be colored orange. Moving the slider to `200` must visibly shift the color split (more points become steelblue).

