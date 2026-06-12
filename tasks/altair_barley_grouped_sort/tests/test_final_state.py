import json
import os
import re
import subprocess

import pytest

PROJECT_DIR = "/home/user/altair_task"
BUILD_SCRIPT = os.path.join(PROJECT_DIR, "build_chart.py")
OUTPUT_HTML = os.path.join(PROJECT_DIR, "output", "chart.html")


# ---------------------------------------------------------------------------
# Setup: execute the build script (truth.Setup).
# ---------------------------------------------------------------------------
@pytest.fixture(scope="session", autouse=True)
def build_chart():
    if os.path.isfile(OUTPUT_HTML):
        os.remove(OUTPUT_HTML)
    result = subprocess.run(
        ["python3", BUILD_SCRIPT],
        capture_output=True,
        text=True,
        cwd=PROJECT_DIR,
    )
    assert result.returncode == 0, (
        f"build_chart.py failed (exit {result.returncode}).\n"
        f"STDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
    )
    assert os.path.isfile(OUTPUT_HTML), (
        f"build_chart.py did not produce {OUTPUT_HTML}.\n"
        f"STDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
    )
    yield


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _extract_vegalite_spec(html_path: str) -> dict:
    """Extract the embedded Vega-Lite JSON spec from an Altair-exported HTML page."""
    with open(html_path, "r", encoding="utf-8") as f:
        html = f.read()

    # Altair's HTML template embeds the spec either as
    #   var spec = {...};
    # or via JSON.parse("...") inside a script block. Cover both shapes.
    candidates = []

    # Pattern 1: var spec = { ... };  (most common)
    m = re.search(r"var\s+spec\s*=\s*(\{.*?\})\s*;\s*var\s+embedOpt", html, re.DOTALL)
    if m:
        candidates.append(m.group(1))

    # Pattern 2: vegaEmbed("#vis", { ... }, opt) inline
    if not candidates:
        for m in re.finditer(r"vegaEmbed\s*\(\s*[\"'][^\"']+[\"']\s*,\s*(\{.*?\})\s*,",
                              html, re.DOTALL):
            candidates.append(m.group(1))

    # Pattern 3: any large balanced JSON object that contains "$schema": "https://vega.github.io/schema/vega-lite"
    if not candidates:
        for m in re.finditer(r"(\{[^\n]*\$schema[^\n]*vega-lite[^\n]*\})", html):
            candidates.append(m.group(1))

    last_error: Exception | None = None
    for raw in candidates:
        try:
            return json.loads(raw)
        except Exception as e:  # pragma: no cover - debugging aid
            last_error = e

    raise AssertionError(
        "Could not extract a Vega-Lite JSON spec from chart.html. "
        f"Tried {len(candidates)} candidate(s). Last error: {last_error}"
    )


def _walk(obj):
    """Yield every nested dict/list contained in obj (and obj itself)."""
    if isinstance(obj, dict):
        yield obj
        for v in obj.values():
            yield from _walk(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from _walk(v)


def _mark_type(mark) -> str | None:
    if isinstance(mark, str):
        return mark
    if isinstance(mark, dict):
        t = mark.get("type")
        if isinstance(t, str):
            return t
    return None


def _find_layers_with_mark(spec: dict, mark_types: set[str]) -> list[dict]:
    """Find every dict node that has a `mark` whose type matches one of `mark_types`."""
    matches = []
    for node in _walk(spec):
        if isinstance(node, dict) and "mark" in node:
            mt = _mark_type(node["mark"])
            if mt in mark_types:
                matches.append(node)
    return matches


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------
@pytest.fixture(scope="session")
def spec() -> dict:
    return _extract_vegalite_spec(OUTPUT_HTML)


def test_dataset_is_barley(spec):
    """truth.2: the chart's data references the barley dataset."""
    found = False
    for node in _walk(spec):
        if isinstance(node, dict):
            data = node.get("data")
            if isinstance(data, dict):
                url = data.get("url", "")
                name = data.get("name", "")
                if "barley" in str(url).lower() or "barley" in str(name).lower():
                    found = True
                    break
            # Some named-dataset references appear as {"name": "..."} at the top level
            if "datasets" in node and isinstance(node["datasets"], dict):
                for k, v in node["datasets"].items():
                    if "barley" in str(k).lower():
                        found = True
                        break
    assert found, (
        "Embedded spec does not reference the 'barley' dataset (no data.url or data.name "
        "mentioning 'barley')."
    )


def test_facet_by_year(spec):
    """truth.3: the spec facets by year (ordinal/temporal)."""
    facet_nodes = []
    for node in _walk(spec):
        if not isinstance(node, dict):
            continue
        # Pattern A: top-level facet spec ({facet: {...}, spec: {...}})
        if "facet" in node and "spec" in node:
            facet_nodes.append(node["facet"])
        # Pattern B: facet/row/column as encoding channels
        enc = node.get("encoding")
        if isinstance(enc, dict):
            for ch in ("facet", "row", "column"):
                if ch in enc and isinstance(enc[ch], dict):
                    facet_nodes.append(enc[ch])

    assert facet_nodes, "No facet/row/column definition found in the spec."

    def _matches_year(fnode: dict) -> bool:
        # facet may itself be {"field": "year", ...} or {"row": {...}, "column": {...}}
        if fnode.get("field") == "year":
            t = fnode.get("type", "ordinal")
            return t in ("ordinal", "temporal", "nominal")
        for sub_key in ("row", "column", "facet"):
            sub = fnode.get(sub_key)
            if isinstance(sub, dict) and sub.get("field") == "year":
                t = sub.get("type", "ordinal")
                return t in ("ordinal", "temporal", "nominal")
        return False

    assert any(_matches_year(fn) for fn in facet_nodes), (
        f"Spec is not faceted on field 'year'. Found facet nodes: {facet_nodes}"
    )


def test_grouped_bar_layer(spec):
    """truth.4: the bar layer encodes the grouped-bar requirements."""
    bar_layers = _find_layers_with_mark(spec, {"bar"})
    assert bar_layers, "No layer with mark 'bar' found in the spec."

    matching = []
    for layer in bar_layers:
        enc = layer.get("encoding", {})
        if not isinstance(enc, dict):
            continue
        x = enc.get("x", {})
        y = enc.get("y", {})
        xoff = enc.get("xOffset", {})
        color = enc.get("color", {})
        if not all(isinstance(c, dict) for c in (x, y, xoff, color)):
            continue
        if (
            x.get("field") == "site"
            and x.get("type") == "nominal"
            and y.get("field") == "yield"
            and y.get("aggregate") == "mean"
            and y.get("type") == "quantitative"
            and xoff.get("field") == "variety"
            and color.get("field") == "variety"
        ):
            matching.append(layer)

    assert matching, (
        "No bar layer matches the required grouped-bar encoding (x=site:N, y=mean(yield):Q, "
        f"xOffset=variety, color=variety). Bar layers found: {bar_layers}"
    )

    layer = matching[0]
    x_sort = layer["encoding"]["x"].get("sort")
    assert isinstance(x_sort, dict), (
        f"x.sort must be an object with field/op/order, got: {x_sort!r}"
    )
    assert x_sort.get("field") == "yield", (
        f"x.sort.field must be 'yield', got: {x_sort.get('field')!r}"
    )
    assert x_sort.get("op") == "mean", (
        f"x.sort.op must be 'mean', got: {x_sort.get('op')!r}"
    )
    assert x_sort.get("order") == "descending", (
        f"x.sort.order must be 'descending', got: {x_sort.get('order')!r}"
    )

    color = layer["encoding"]["color"]
    scale = color.get("scale", {})
    assert isinstance(scale, dict) and scale.get("scheme") == "tableau10", (
        f"color.scale.scheme must be 'tableau10', got: {scale!r}"
    )


def test_mean_overlay_layer(spec):
    """truth.5: a tick or rule layer aggregates mean(yield) grouped by site (and year)."""
    overlay_candidates = _find_layers_with_mark(spec, {"tick", "rule"})
    assert overlay_candidates, (
        "No 'tick' or 'rule' layer found for the per-site mean overlay."
    )

    def _has_required_aggregate(layer: dict) -> bool:
        transforms = layer.get("transform")
        if not isinstance(transforms, list):
            return False
        for t in transforms:
            if not isinstance(t, dict):
                continue
            agg = t.get("aggregate")
            groupby = t.get("groupby")
            if not isinstance(agg, list) or not isinstance(groupby, list):
                continue
            mean_yield = any(
                isinstance(a, dict)
                and a.get("op") == "mean"
                and a.get("field") == "yield"
                for a in agg
            )
            grouped_by_site = "site" in groupby
            grouped_by_year = "year" in groupby
            if mean_yield and grouped_by_site and grouped_by_year:
                return True
        return False

    matching = [layer for layer in overlay_candidates if _has_required_aggregate(layer)]
    assert matching, (
        "Found tick/rule layer(s), but none uses a transform_aggregate with "
        "{op:'mean', field:'yield'} grouped by ['site', 'year']. "
        f"Candidates: {overlay_candidates}"
    )


def test_title_has_text_and_subtitle(spec):
    """truth.6: top-level title is an object with non-empty text and subtitle."""
    title = spec.get("title")
    assert isinstance(title, dict), (
        f"Top-level title must be an object with 'text' and 'subtitle', got: {type(title).__name__} ({title!r})"
    )
    text = title.get("text")
    subtitle = title.get("subtitle")
    assert isinstance(text, (str, list)) and text, (
        f"title.text must be a non-empty string or list, got: {text!r}"
    )
    assert isinstance(subtitle, (str, list)) and subtitle, (
        f"title.subtitle must be a non-empty string or list, got: {subtitle!r}"
    )


def test_browser_renders_grouped_bars_and_ticks():
    """truth.7: pochi-verifier confirms grouped bars across year facets and tick marks."""
    from pochi_verifier import PochiVerifier  # type: ignore

    reason = (
        "The Altair-exported HTML at /home/user/altair_task/output/chart.html must render "
        "a faceted grouped bar chart of the barley dataset (one panel per year) with "
        "narrow grouped bars per site colored by variety, and a per-site mean tick overlay."
    )
    truth = (
        "Open file:///home/user/altair_task/output/chart.html in the browser. "
        "Verify a Vega-Lite visualization renders (SVG or canvas). "
        "Verify at least two facet panels are visible, each labeled by a year value. "
        "Within each facet, verify that for every site on the x-axis there are multiple "
        "thin grouped bars side-by-side (NOT a single stacked bar), with a color legend "
        "labelled by variety. "
        "Verify that a short horizontal tick (or rule) mark is visible over each site, "
        "indicating the per-site mean yield."
    )

    verifier = PochiVerifier()
    result = verifier.verify(
        reason=reason,
        truth=truth,
        use_browser_agent=True,
        trajectory_dir="/logs/verifier/pochi/test_browser_renders_grouped_bars_and_ticks",
    )
    assert result.status == "pass", f"Browser verification failed: {result.reason}"
