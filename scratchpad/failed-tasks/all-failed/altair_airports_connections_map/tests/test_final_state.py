import json
import os
import re
import subprocess

import pytest

PROJECT_DIR = "/home/user/myproject"
CHART_HTML = os.path.join(PROJECT_DIR, "chart.html")
CHART_SCRIPT = os.path.join(PROJECT_DIR, "chart.py")


# ---------------------------------------------------------------------------
# Spec extraction helpers
# ---------------------------------------------------------------------------


def _resolve_dataset_urls():
    """Resolve the canonical URLs Altair uses for the relevant datasets."""
    result = subprocess.run(
        [
            "python3",
            "-c",
            (
                "from vega_datasets import data;"
                "import json;"
                "print(json.dumps({"
                "'airports': data.airports.url,"
                "'flights_airport': data.flights_airport.url,"
                "'us_10m': data.us_10m.url"
                "}))"
            ),
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        f"Failed to resolve vega_datasets URLs: stderr={result.stderr!r}"
    )
    return json.loads(result.stdout.strip())


def _extract_json_object(text: str, start: int) -> str:
    """Extract a balanced JSON object literal starting at `start` (must point at '{')."""
    assert text[start] == "{", "Expected JSON object to start with '{'."
    depth = 0
    in_str = False
    esc = False
    for i in range(start, len(text)):
        ch = text[i]
        if in_str:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == '"':
                in_str = False
            continue
        if ch == '"':
            in_str = True
        elif ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return text[start : i + 1]
    raise AssertionError("Unbalanced braces while extracting JSON spec.")


def _load_spec(html: str) -> dict:
    """Locate the embedded Vega-Lite spec inside the HTML produced by Altair."""
    # Altair's HTML template emits the spec as a JS object literal assigned to
    # a variable named `spec`. Cover the common declaration prefixes.
    pattern = re.compile(r"(?:var|let|const)\s+spec\s*=\s*", re.MULTILINE)
    match = pattern.search(html)
    if not match:
        # Fallback: vegaEmbed("#vis", {...}, ...)
        embed = re.search(r"vegaEmbed\s*\([^,]+,\s*", html)
        assert embed, "Could not locate spec literal in chart.html"
        brace_start = html.find("{", embed.end())
    else:
        brace_start = html.find("{", match.end())
    assert brace_start != -1, "Could not locate spec opening brace in chart.html"
    raw = _extract_json_object(html, brace_start)
    return json.loads(raw)


def _collect_layers(spec: dict) -> list[dict]:
    """Flatten nested `layer` arrays into a list of single-mark sub-specs."""
    layers: list[dict] = []

    def walk(node):
        if isinstance(node, dict):
            if "layer" in node and isinstance(node["layer"], list):
                for sub in node["layer"]:
                    walk(sub)
            else:
                layers.append(node)

    walk(spec)
    return layers


def _mark_type(layer: dict):
    mark = layer.get("mark")
    if isinstance(mark, dict):
        return mark.get("type")
    return mark


def _data_url(layer: dict, spec: dict) -> str | None:
    data = layer.get("data") or spec.get("data") or {}
    if isinstance(data, dict):
        return data.get("url")
    return None


def _collect_params(spec: dict) -> list[dict]:
    """Collect all `params` entries from the spec, top-level + every sub-layer."""
    params: list[dict] = []

    def walk(node):
        if isinstance(node, dict):
            ps = node.get("params")
            if isinstance(ps, list):
                params.extend(p for p in ps if isinstance(p, dict))
            for value in node.values():
                walk(value)
        elif isinstance(node, list):
            for item in node:
                walk(item)

    walk(spec)
    return params


def _collect_projections(spec: dict) -> list[dict]:
    projections: list[dict] = []

    def walk(node):
        if isinstance(node, dict):
            proj = node.get("projection")
            if isinstance(proj, dict):
                projections.append(proj)
            for value in node.values():
                walk(value)
        elif isinstance(node, list):
            for item in node:
                walk(item)

    walk(spec)
    return projections


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def generated_html() -> str:
    # Re-run the executor's script to regenerate the output deterministically.
    if os.path.exists(CHART_HTML):
        os.remove(CHART_HTML)
    assert os.path.isfile(CHART_SCRIPT), f"Missing chart script at {CHART_SCRIPT}"
    proc = subprocess.run(
        ["python3", "chart.py"],
        cwd=PROJECT_DIR,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, (
        f"Executing chart.py failed: stdout={proc.stdout!r} stderr={proc.stderr!r}"
    )
    assert os.path.isfile(CHART_HTML), (
        f"Expected {CHART_HTML} to be produced by chart.py."
    )
    with open(CHART_HTML, "r", encoding="utf-8") as fh:
        return fh.read()


@pytest.fixture(scope="module")
def spec(generated_html: str) -> dict:
    return _load_spec(generated_html)


@pytest.fixture(scope="module")
def layers(spec: dict) -> list[dict]:
    return _collect_layers(spec)


@pytest.fixture(scope="module")
def dataset_urls() -> dict:
    return _resolve_dataset_urls()


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_chart_html_exists_and_non_empty(generated_html: str):
    assert len(generated_html.strip()) > 0, "chart.html is empty."
    assert "vegaEmbed" in generated_html, (
        "chart.html does not look like an Altair/Vega-Embed HTML page (missing 'vegaEmbed')."
    )


def test_projection_is_albers_usa(spec: dict):
    projections = _collect_projections(spec)
    assert projections, "Spec does not declare a projection."
    types = [p.get("type") for p in projections]
    assert "albersUsa" in types, (
        f"Expected projection type 'albersUsa', found projections: {projections}."
    )


def test_geoshape_layer_uses_states_topojson(layers: list[dict], dataset_urls: dict):
    geoshape_layers = [l for l in layers if _mark_type(l) == "geoshape"]
    assert geoshape_layers, "No geoshape mark layer found in the spec."
    matched = False
    for layer in geoshape_layers:
        data = layer.get("data") or {}
        url = data.get("url") if isinstance(data, dict) else None
        fmt = data.get("format") if isinstance(data, dict) else None
        if (
            url == dataset_urls["us_10m"]
            and isinstance(fmt, dict)
            and fmt.get("feature") == "states"
        ):
            matched = True
            break
    assert matched, (
        "No geoshape layer reads data.us_10m.url with format.feature == 'states'. "
        f"Found geoshape layers: {[l.get('data') for l in geoshape_layers]}"
    )


def test_circle_layer_from_airports_with_lat_long(
    layers: list[dict], dataset_urls: dict, spec: dict
):
    circle_layers = [l for l in layers if _mark_type(l) == "circle"]
    assert circle_layers, "No circle mark layer found in the spec."
    valid = []
    for layer in circle_layers:
        enc = layer.get("encoding") or {}
        if "latitude" not in enc or "longitude" not in enc:
            continue
        url = _data_url(layer, spec)
        if url == dataset_urls["airports"]:
            valid.append(layer)
    assert valid, (
        "No circle layer reads from data.airports.url with both 'latitude' and "
        f"'longitude' encodings. Circle layers found: {circle_layers}"
    )


def test_rule_layer_has_four_geo_encodings(layers: list[dict], dataset_urls: dict, spec: dict):
    rule_layers = [l for l in layers if _mark_type(l) == "rule"]
    assert rule_layers, "No rule mark layer found in the spec."
    matched = None
    required = {"latitude", "longitude", "latitude2", "longitude2"}
    for layer in rule_layers:
        enc = layer.get("encoding") or {}
        if required.issubset(enc.keys()):
            url = _data_url(layer, spec)
            if url == dataset_urls["flights_airport"]:
                matched = layer
                break
    assert matched is not None, (
        "No rule layer with latitude+longitude+latitude2+longitude2 encodings reading "
        f"from data.flights_airport.url. Rule layers: {rule_layers}"
    )


def test_rule_layer_has_two_lookups_origin_and_destination(
    layers: list[dict], dataset_urls: dict, spec: dict
):
    rule_layers = [
        l
        for l in layers
        if _mark_type(l) == "rule"
        and _data_url(l, spec) == dataset_urls["flights_airport"]
    ]
    assert rule_layers, "Rule layer reading from flights_airport.url not found."
    rule = rule_layers[0]
    transforms = rule.get("transform") or []
    lookups = [t for t in transforms if isinstance(t, dict) and "lookup" in t]
    assert len(lookups) == 2, (
        f"Expected exactly two lookup transforms on the rule layer, got {len(lookups)}: "
        f"{lookups}"
    )
    lookup_keys = sorted(t.get("lookup") for t in lookups)
    assert lookup_keys == ["destination", "origin"], (
        f"Expected lookup keys {{'origin', 'destination'}}, got {lookup_keys}."
    )


def test_click_selection_on_origin_field(spec: dict):
    params = _collect_params(spec)
    selections = []
    for p in params:
        sel = p.get("select")
        if isinstance(sel, dict) and sel.get("type") == "point":
            selections.append((p, sel))
        elif sel == "point":
            selections.append((p, {"type": "point"}))
    assert selections, "No point selection parameter declared in the spec."
    matching = []
    for param, sel in selections:
        fields = sel.get("fields")
        on = sel.get("on")
        empty = sel.get("empty")
        if (
            fields == ["origin"]
            and isinstance(on, str)
            and "click" in on
            and empty is False
        ):
            matching.append(param)
    assert matching, (
        "No point selection with fields=['origin'], on containing 'click', and empty=False. "
        f"Found selections: {selections}"
    )


def test_route_layer_is_gated_by_selection(layers: list[dict], spec: dict, dataset_urls: dict):
    # Identify the selection parameter name(s) we expect to gate the route layer.
    params = _collect_params(spec)
    selection_names = []
    for p in params:
        sel = p.get("select")
        if isinstance(sel, dict) and sel.get("type") == "point" and sel.get("fields") == ["origin"]:
            selection_names.append(p.get("name"))
    assert selection_names, "Could not identify origin-click selection by name."

    rule_layers = [
        l
        for l in layers
        if _mark_type(l) == "rule"
        and _data_url(l, spec) == dataset_urls["flights_airport"]
    ]
    assert rule_layers, "No rule layer to check selection gating against."
    rule = rule_layers[0]
    transforms = rule.get("transform") or []

    def _references_selection(value) -> bool:
        if isinstance(value, dict):
            if value.get("param") in selection_names:
                return True
            for v in value.values():
                if _references_selection(v):
                    return True
        elif isinstance(value, list):
            for v in value:
                if _references_selection(v):
                    return True
        elif isinstance(value, str):
            return any(name in value for name in selection_names if name)
        return False

    filter_gated = any(
        isinstance(t, dict) and "filter" in t and _references_selection(t["filter"])
        for t in transforms
    )

    opacity_gated = False
    enc = rule.get("encoding") or {}
    opacity = enc.get("opacity")
    if isinstance(opacity, dict):
        condition = opacity.get("condition")
        if _references_selection(condition):
            opacity_gated = True

    assert filter_gated or opacity_gated, (
        "Rule layer is not gated by the origin selection (no transform_filter on the "
        "selection and no conditional opacity tied to the selection)."
    )


def test_browser_render_contains_geo_and_marks():
    """Browser verification via pochi-verifier (geo paths + circles + click-driven rules)."""
    try:
        from pochi_verifier import PochiVerifier
    except Exception:
        pytest.skip("pochi_verifier not available in this environment.")

    verifier = PochiVerifier()
    reason = (
        "The generated chart.html must render an interactive US airports connections map "
        "built with Vega-Altair. The page must show a US states geographic background, "
        "circle marks for airports across the country, and route lines that only appear "
        "after clicking an airport circle."
    )
    truth = (
        "Open file:///home/user/myproject/chart.html in the browser. Wait for the chart "
        "to render. Verify that: "
        "(1) the chart container shows a US map (multiple SVG path elements forming state "
        "shapes); "
        "(2) many small circle marks are visible on top of the map representing airports; "
        "(3) before any interaction, no flight route lines (rule marks) are visible; "
        "(4) clicking a single airport circle causes one or more straight route lines "
        "to appear, connecting that airport to other airports on the map; "
        "(5) clicking on empty map background hides the route lines again."
    )
    result = verifier.verify(
        reason=reason,
        truth=truth,
        use_browser_agent=True,
        trajectory_dir="/logs/verifier/pochi/test_browser_render_contains_geo_and_marks",
    )
    assert result.status == "pass", f"Browser verification failed: {result.reason}"
