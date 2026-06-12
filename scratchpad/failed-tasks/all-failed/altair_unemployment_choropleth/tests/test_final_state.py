import json
import os
import re

import pytest
from pochi_verifier import PochiVerifier

PROJECT_DIR = "/home/user/myproject"
CHART_HTML = os.path.join(PROJECT_DIR, "chart.html")


def _extract_spec(html_text: str) -> dict:
    """Extract the embedded Vega-Lite spec object from an Altair-generated HTML file.

    Altair's default save() template embeds the spec via either:
        var spec = {...};
    or directly as an argument to vegaEmbed(...). This helper handles the
    common ``var spec = {...};`` shape produced by ``chart.save('chart.html')``.
    """
    match = re.search(r"var\s+spec\s*=\s*", html_text)
    if not match:
        # Fall back to JSON object passed inline to vegaEmbed("#vis", {...}, ...)
        match = re.search(r"vegaEmbed\(\s*[\"']#vis[\"']\s*,\s*", html_text)
        assert match, (
            "Could not locate the embedded Vega-Lite spec inside chart.html. "
            "Expected either 'var spec = {...}' or vegaEmbed('#vis', {...}, ...)."
        )

    start = match.end()
    # Skip whitespace
    while start < len(html_text) and html_text[start].isspace():
        start += 1
    assert start < len(html_text) and html_text[start] == "{", (
        "Embedded Vega-Lite spec is not a JSON object."
    )

    depth = 0
    in_string = False
    escape = False
    end = None
    for i in range(start, len(html_text)):
        ch = html_text[i]
        if in_string:
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == '"':
                in_string = False
            continue
        if ch == '"':
            in_string = True
            continue
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                end = i + 1
                break
    assert end is not None, "Failed to find balanced braces for the Vega-Lite spec."

    spec_text = html_text[start:end]
    return json.loads(spec_text)


def _iter_children(spec: dict):
    """Yield every chart node inside the top-level spec (including the root)."""
    stack = [spec]
    while stack:
        node = stack.pop()
        if not isinstance(node, dict):
            continue
        yield node
        for key in ("vconcat", "hconcat", "concat", "layer"):
            children = node.get(key)
            if isinstance(children, list):
                stack.extend(children)
        for key in ("spec",):
            child = node.get(key)
            if isinstance(child, dict):
                stack.append(child)


def _mark_type(node: dict) -> str | None:
    mark = node.get("mark")
    if isinstance(mark, str):
        return mark
    if isinstance(mark, dict):
        return mark.get("type")
    return None


def _normalize_tooltip_fields(tooltip) -> list[str]:
    if tooltip is None:
        return []
    if isinstance(tooltip, dict):
        tooltip = [tooltip]
    fields: list[str] = []
    if isinstance(tooltip, list):
        for entry in tooltip:
            if isinstance(entry, dict) and "field" in entry:
                fields.append(str(entry["field"]))
    return fields


@pytest.fixture(scope="session")
def chart_spec() -> dict:
    assert os.path.isfile(CHART_HTML), (
        f"Expected solver to create {CHART_HTML} but the file was not found."
    )
    assert os.path.getsize(CHART_HTML) > 0, f"{CHART_HTML} is empty."
    with open(CHART_HTML, "r", encoding="utf-8") as fh:
        html_text = fh.read()
    return _extract_spec(html_text)


@pytest.fixture(scope="session")
def map_and_histogram(chart_spec: dict):
    # The top-level spec must contain a concatenated layout with at least two children.
    layout_children = None
    for key in ("vconcat", "hconcat", "concat"):
        if isinstance(chart_spec.get(key), list) and len(chart_spec[key]) >= 2:
            layout_children = chart_spec[key]
            break
    assert layout_children is not None, (
        "Top-level spec must be a vconcat/hconcat/concat layout with at least two children."
    )

    map_chart = None
    hist_chart = None
    for node in _iter_children(chart_spec):
        mark = _mark_type(node)
        if mark == "geoshape" and map_chart is None:
            map_chart = node
        elif mark == "bar" and hist_chart is None:
            hist_chart = node
    assert map_chart is not None, "No geoshape (map) chart found in the spec."
    assert hist_chart is not None, "No bar (histogram) chart found in the spec."
    return map_chart, hist_chart


def test_chart_html_exists():
    assert os.path.isfile(CHART_HTML), f"{CHART_HTML} must exist after running solution.py."
    assert os.path.getsize(CHART_HTML) > 0, f"{CHART_HTML} must not be empty."


def test_map_uses_lookup_transform_referencing_unemployment(map_and_histogram):
    map_chart, _ = map_and_histogram
    transforms = map_chart.get("transform", [])
    assert isinstance(transforms, list) and transforms, (
        "Map chart must have a non-empty 'transform' list."
    )
    lookup_entries = [t for t in transforms if isinstance(t, dict) and "lookup" in t]
    assert lookup_entries, (
        "Map chart must include a transform_lookup entry."
    )
    found = False
    for entry in lookup_entries:
        from_ = entry.get("from", {})
        data = from_.get("data", {}) if isinstance(from_, dict) else {}
        url = data.get("url", "") if isinstance(data, dict) else ""
        fields = from_.get("fields", []) if isinstance(from_, dict) else []
        if "unemployment" in str(url) and "rate" in [str(f) for f in (fields or [])]:
            found = True
            break
    assert found, (
        "Map chart's lookup transform must reference an unemployment dataset URL "
        "and pull in the 'rate' field."
    )


def test_map_projection_is_albers_usa(map_and_histogram):
    map_chart, _ = map_and_histogram
    projection = map_chart.get("projection", {})
    assert isinstance(projection, dict), "Map chart must have a 'projection' object."
    assert projection.get("type") == "albersUsa", (
        f"Map projection.type must be 'albersUsa', got {projection.get('type')!r}."
    )


def test_map_color_threshold_blues(map_and_histogram):
    map_chart, _ = map_and_histogram
    encoding = map_chart.get("encoding", {})
    color = encoding.get("color", {})
    assert isinstance(color, dict), "Map color encoding must be an object."
    assert color.get("field") == "rate", (
        f"Map color encoding field must be 'rate', got {color.get('field')!r}."
    )
    assert color.get("type") == "quantitative", (
        f"Map color encoding type must be 'quantitative', got {color.get('type')!r}."
    )
    scale = color.get("scale", {})
    assert isinstance(scale, dict), "Map color encoding must include a scale object."
    assert scale.get("type") == "threshold", (
        f"Map color scale.type must be 'threshold', got {scale.get('type')!r}."
    )
    scheme = scale.get("scheme")
    scheme_name = scheme.get("name") if isinstance(scheme, dict) else scheme
    assert isinstance(scheme_name, str) and scheme_name.lower() == "blues", (
        f"Map color scale.scheme must be 'blues' (case-insensitive), got {scheme!r}."
    )
    domain = scale.get("domain")
    assert isinstance(domain, list) and len(domain) >= 3, (
        f"Map color scale.domain must list at least 3 numeric break points, got {domain!r}."
    )
    assert all(isinstance(v, (int, float)) for v in domain), (
        "All threshold break points must be numeric."
    )


def test_map_tooltip_has_id_and_rate(map_and_histogram):
    map_chart, _ = map_and_histogram
    encoding = map_chart.get("encoding", {})
    tooltip_fields = _normalize_tooltip_fields(encoding.get("tooltip"))
    assert "id" in tooltip_fields, (
        f"Map tooltip must include the 'id' field; got fields={tooltip_fields!r}."
    )
    assert "rate" in tooltip_fields, (
        f"Map tooltip must include the 'rate' field; got fields={tooltip_fields!r}."
    )


def test_map_filter_references_brush_param(map_and_histogram):
    map_chart, hist_chart = map_and_histogram
    transforms = map_chart.get("transform", [])
    filter_param_names: list[str] = []
    for entry in transforms:
        if not isinstance(entry, dict):
            continue
        flt = entry.get("filter")
        if isinstance(flt, dict) and "param" in flt:
            filter_param_names.append(str(flt["param"]))
        elif isinstance(flt, str):
            # Some compilers may emit a string predicate; record it for fallback matching.
            filter_param_names.append(flt)
    assert filter_param_names, (
        "Map chart must include a transform_filter that references a selection parameter."
    )

    hist_params = hist_chart.get("params", [])
    assert isinstance(hist_params, list) and hist_params, (
        "Histogram chart must declare an interval selection param via add_params."
    )
    hist_param_names = [p.get("name") for p in hist_params if isinstance(p, dict)]
    overlap = set(filter_param_names) & set(filter(None, hist_param_names))
    assert overlap, (
        f"Map filter param(s) {filter_param_names!r} must match a histogram param name "
        f"(histogram params: {hist_param_names!r})."
    )


def test_histogram_has_interval_brush_on_binned_rate(map_and_histogram):
    _, hist_chart = map_and_histogram
    encoding = hist_chart.get("encoding", {})
    x_enc = encoding.get("x", {})
    assert isinstance(x_enc, dict), "Histogram must have an x-encoding object."
    assert x_enc.get("field") == "rate", (
        f"Histogram x-encoding must bind to the 'rate' field, got {x_enc.get('field')!r}."
    )
    bin_spec = x_enc.get("bin")
    assert bin_spec, (
        f"Histogram x-encoding must set bin to true or a bin spec, got {bin_spec!r}."
    )

    y_enc = encoding.get("y", {})
    assert isinstance(y_enc, dict), "Histogram must have a y-encoding object."
    assert y_enc.get("aggregate") == "count" or y_enc.get("field") == "*" and y_enc.get(
        "aggregate"
    ) == "count", (
        f"Histogram y-encoding must use a count aggregate, got {y_enc!r}."
    )

    params = hist_chart.get("params", [])
    interval_params = [
        p for p in params
        if isinstance(p, dict)
        and isinstance(p.get("select"), dict)
        and p["select"].get("type") == "interval"
    ]
    assert interval_params, (
        f"Histogram must register an interval selection param, got params={params!r}."
    )


def test_browser_render():
    reason = (
        "Altair must render the choropleth+histogram dashboard cleanly in a browser. "
        "Vega-Embed should produce a #vis container populated with SVG or canvas elements, "
        "and the page should not raise any JavaScript errors."
    )
    truth = (
        f"Navigate to file://{CHART_HTML}. Wait for Vega-Embed to finish rendering. "
        "Verify that a div with id 'vis' exists and contains at least one descendant SVG or "
        "canvas element produced by Vega-Embed (e.g. an svg.marks node or a canvas element). "
        "Verify that no JavaScript console errors were emitted while loading or rendering."
    )
    verifier = PochiVerifier()
    result = verifier.verify(
        reason=reason,
        truth=truth,
        use_browser_agent=True,
        trajectory_dir="/logs/verifier/pochi/test_browser_render",
    )
    assert result.status == "pass", f"Browser verification failed: {result.reason}"
