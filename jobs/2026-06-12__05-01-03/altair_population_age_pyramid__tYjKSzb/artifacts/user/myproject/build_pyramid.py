"""
Back-to-back population age pyramid using Vega-Altair.

Produces pyramid.html and pyramid_spec.json in /home/user/myproject.
"""

import json
import os
import altair as alt

# ---------------------------------------------------------------------------
# 1. Data source  –  embed the canonical vega-datasets URL directly so the
#    spec references it (no pandas pre-loading).
# ---------------------------------------------------------------------------
POPULATION_URL = "https://vega.github.io/vega-datasets/data/population.json"

# ---------------------------------------------------------------------------
# 2. Year-selector parameter  –  options are all distinct census years in the
#    dataset (1850 … 2000 in steps of 10).  Initial value = 1980.
# ---------------------------------------------------------------------------
years = list(range(1850, 2010, 10))

year_param = alt.param(
    name="year_param",
    value=1980,
    bind=alt.binding_select(options=years, name="Census year: "),
)

# ---------------------------------------------------------------------------
# 3. Build the chart
# ---------------------------------------------------------------------------
pyramid = (
    alt.Chart(alt.UrlData(url=POPULATION_URL))
    # -- 3a. Compute signed_people: negative for males, positive for females --
    .transform_calculate(
        signed_people="datum.sex === 1 ? -datum.people : datum.people"
    )
    # -- 3b. Keep only the selected year ---------------------------------
    .transform_filter("datum.year == year_param")
    # -- 3c. Bar mark ----------------------------------------------------
    .mark_bar()
    # -- 3d. Encodings ---------------------------------------------------
    .encode(
        # X: quantitative on signed_people; axis labels show absolute values
        x=alt.X(
            "signed_people:Q",
            title="Population",
            axis=alt.Axis(
                format="~s",          # SI suffix  (e.g. 10M)
                labelExpr="abs(datum.value)",   # strip the minus sign
            ),
        ),
        # Y: ordinal age buckets, oldest at the top
        y=alt.Y(
            "age:O",
            title="Age",
            sort="descending",        # largest age value at top
        ),
        # Color: 1 = Male (steelblue), 2 = Female (salmon)
        color=alt.Color(
            "sex:N",
            scale=alt.Scale(
                domain=[1, 2],
                range=["steelblue", "salmon"],
            ),
            legend=alt.Legend(
                title="Sex",
                labelExpr="datum.value == 1 ? 'Male' : 'Female'",
            ),
        ),
    )
    # -- 3e. Attach the year parameter -----------------------------------
    .add_params(year_param)
    .properties(
        title="US Population Age Pyramid",
        width=500,
        height=400,
    )
)

# ---------------------------------------------------------------------------
# 4. Save outputs
# ---------------------------------------------------------------------------
out_dir = os.path.dirname(os.path.abspath(__file__))
html_path = os.path.join(out_dir, "pyramid.html")
json_path = os.path.join(out_dir, "pyramid_spec.json")

pyramid.save(html_path)
print(f"Saved HTML  →  {html_path}")

spec = pyramid.to_dict()
with open(json_path, "w", encoding="utf-8") as fh:
    json.dump(spec, fh, indent=2)
print(f"Saved JSON  →  {json_path}")


def main() -> None:
    # Everything already executed at module level above; this entry point
    # exists so the script can also be called via `python build_pyramid.py`.
    pass


if __name__ == "__main__":
    main()
