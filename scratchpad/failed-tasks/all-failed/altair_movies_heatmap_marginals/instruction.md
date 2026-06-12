# Movies 2D Heatmap with Marginal Histograms (Vega-Altair)

## Background
The analytics team wants a single dashboard for exploring how IMDB ratings and Rotten Tomatoes ratings co-vary across movies. They have asked for a 2D binned heatmap together with marginal histograms on the top and right, and they want to be able to drag out a rectangular region on the heatmap so the marginal histograms show how many records fall inside the brushed 2D region versus the total. Build this with Vega-Altair and export the result as a static HTML file.

## Requirements
- Use the `vega_datasets` movies dataset as a URL data source: `data.movies.url` (from `vega_datasets`).
- Produce a Vega-Altair compound chart with three subplots arranged like this:
  - Top: a marginal histogram of `IMDB_Rating` that lines up horizontally with the heatmap below it.
  - Center: a 2D binned heatmap of `IMDB_Rating` (x axis) vs `Rotten_Tomatoes_Rating` (y axis), colored by the number of movies in each 2D bin.
  - Right: a marginal histogram of `Rotten_Tomatoes_Rating` that lines up vertically with the heatmap (the bars run horizontally, i.e. count on x, binned rating on y).
- Both axes of the heatmap must be binned with `maxbins=20`, and the heatmap mark must be `rect`.
- The color encoding of the heatmap must use the `count()` aggregate with the `viridis` color scheme.
- Add an interval selection on the heatmap that is projected onto both `x` and `y` (a 2D rectangular brush). Both marginal histograms must react to this brush.
- Each marginal histogram must be a layered chart with two bars per bin:
  - A baseline gray bar showing the total count for that bin across the whole dataset.
  - A second colored bar on top that uses `transform_filter` referencing the brush parameter so that it only counts records that fall inside the brushed 2D region.
- Save the final compound chart to `/home/user/myproject/chart.html` using `chart.save(...)`.

## Implementation Hints
- Use `vega_datasets` to obtain the movies URL; for URL data sources, you must declare encoding types explicitly (e.g. `IMDB_Rating:Q`).
- Choose appropriate Altair composition primitives so the top histogram shares the heatmap's x axis and the right histogram shares its y axis (vertical and horizontal concatenation).
- An `selection_interval(encodings=['x','y'])` parameter must be added to the heatmap with `add_params(...)`. The same parameter object is then referenced from `transform_filter(...)` on the filtered layer of each marginal histogram.
- For the layered marginals, the bars must have the same bin definition (`maxbins=20`) on the shared axis so the baseline and the filtered layer line up exactly.
- Use a quantitative `count()` encoding on the non-binned channel of the marginals.
- Set the heatmap color scheme to `viridis` via Altair's scale configuration.

## Acceptance Criteria
- Project path: /home/user/myproject
- Command: `python3 build_chart.py`
- Running the command must (re)generate `/home/user/myproject/chart.html`.
- The generated `chart.html` must embed a valid Vega-Lite spec for a compound (concatenated) chart with three subplots: a top marginal histogram, a center heatmap, and a right marginal histogram.
- The center subplot must be a `rect` mark with `IMDB_Rating` on x and `Rotten_Tomatoes_Rating` on y, both binned with `maxbins` approximately 20, colored by a `count` aggregate using the `viridis` scheme.
- The compound spec must declare an interval selection parameter that is projected over both `x` and `y` encodings (a 2D brush) and is attached to the heatmap.
- Each marginal subplot must be a layered chart with at least two bar layers, where one layer contains a `transform_filter` referencing the brush parameter.
- Browser verification: open the generated `chart.html` in a browser; the page must render three visible subplots arranged with a histogram on top, a rectangular heatmap in the middle, and a horizontal-bar histogram on the right; the heatmap area must visibly contain a grid of colored rectangles.

