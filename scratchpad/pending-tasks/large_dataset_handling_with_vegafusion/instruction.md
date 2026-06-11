Altair restricts datasets over 5,000 rows by default (throwing a `MaxRowsError`) to prevent browser crashes from massive JSON payloads. Addressing this is critical for production-grade data science pipelines.

You need to process a synthesized Pandas DataFrame containing 50,000 rows and visualize it as an aggregated 2D heatmap showing record counts.

**Constraints:**
- You MUST explicitly bypass the 5,000-row limit by configuring the environment with `alt.data_transformers.enable('vegafusion')`.
- Do NOT use `alt.data_transformers.disable_max_rows()` as it risks browser lock-up.
- The visualization must aggregate the data into bins on both the X and Y axes within Altair (do not pre-bin in Pandas).
- Save the resulting visualization as `heatmap_large.html`.