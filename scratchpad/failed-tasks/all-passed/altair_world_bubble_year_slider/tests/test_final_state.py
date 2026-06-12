import json
import os
import re
import subprocess

import pytest
from pochi_verifier import PochiVerifier

PROJECT_DIR = "/home/user/myproject"
BUILD_SCRIPT = os.path.join(PROJECT_DIR, "build_chart.py")
CHART_HTML = os.path.join(PROJECT_DIR, "chart.html")
SPEC_JSON = os.path.join(PROJECT_DIR, "spec.json")


@pytest.fixture(scope="session")
def build_outputs():
    """Re-run the build script from a clean state so that the spec/HTML on
    disk are exactly what the executor's script produces."""
    for path in (CHART_HTML, SPEC_JSON):
        if os.path.exists(path):
            os.remove(path)
    assert os.path.isfile(BUILD_SCRIPT), (
        f"Expected build script at {BUILD_SCRIPT}; the task must provide it."
    )
    result = subprocess.run(
        ["python3", "build_chart.py"],
        cwd=PROJECT_DIR,
        capture_output=True,
        text=True,
        timeout=180,
    )
    assert result.returncode == 0, (
        f"`python3 build_chart.py` failed with code {result.returncode}.\n"
        f"stdout: {result.stdout}\nstderr: {result.stderr}"
    )
    return result


@pytest.fixture(scope="session")
def spec(build_outputs):
    assert os.path.isfile(SPEC_JSON), (
        f"Expected Vega-Lite spec file at {SPEC_JSON} after running build_chart.py."
    )
    with open(SPEC_JSON, "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="session")
def chart_html_text(build_outputs):
    assert os.path.isfile(CHART_HTML), (
        f"Expected HTML output at {CHART_HTML} after running build_chart.py."
    )
    with open(CHART_HTML, "r", encoding="utf-8") as f:
        return f.read()


# ---------------------------------------------------------------------------
# Helpers for walking a Vega-Lite spec
# ---------------------------------------------------------------------------

def _iter_subspecs(node):
    """Yield the given dict and every nested chart spec under it."""
    if isinstance(node, dict):
        yield node
        for key in ("layer", "hconcat", "vconcat", "concat", "spec"):
            child = node.get(key)
            if isinstance(child, list):
                for c in child:
                    yield from _iter_subspecs(c)
            elif isinstance(child, dict):
                yield from _iter_subspecs(child)
    elif isinstance(node, list):
        for item in node:
            yield from _iter_subspecs(item)


def _mark_type(sub):
    mark = sub.get("mark")
    if isinstance(mark, str):
        return mark
    if isinstance(mark, dict):
        return mark.get("type")
    return None


def _find_layered_geoshape_and_circle(spec):
    """Return (layered_spec, geoshape_layer, circle_layer) if a layered spec
    with both a geoshape and a circle mark exists anywhere in the tree."""
    for sub in _iter_subspecs(spec):
        layers = sub.get("layer")
        if not isinstance(layers, list):
            continue
        geoshape = None
        circle = None
        for layer in layers:
            # Each layer may itself be a layered spec; flatten one level.
            inner_subspecs = list(_iter_subspecs(layer))
            for inner in inner_subspecs:
                mt = _mark_type(inner)
                if mt == "geoshape" and geoshape is None:
                    geoshape = inner
                if mt == "circle" and circle is None:
                    circle = inner
        if geoshape is not None and circle is not None:
            return sub, geoshape, circle
    return None, None, None


# ---------------------------------------------------------------------------
# Structural spec checks
# ---------------------------------------------------------------------------

def test_layered_chart_has_geoshape_and_circle(spec):
    layered, geoshape, circle = _find_layered_geoshape_and_circle(spec)
    assert layered is not None, (
        "Spec must contain a layered chart with both a geoshape base layer and "
        "a circle bubble layer (top-level `layer`, or layered inside an "
        "`hconcat`/`vconcat` cell)."
    )
    assert geoshape is not None, "Layered chart is missing a geoshape mark."
    assert circle is not None, "Layered chart is missing a circle mark."


def test_projection_is_natural_earth_1(spec):
    layered, _, _ = _find_layered_geoshape_and_circle(spec)
    assert layered is not None, "Could not locate the layered chart."

    # Projection may be set on the layered spec itself or on the enclosing
    # chart spec. Walk up by searching all ancestors that contain the layered
    # spec as a substree.
    candidates = [layered]
    for sub in _iter_subspecs(spec):
        if sub is layered:
            continue
        # Crude ancestor check: serialize and look for unique signature
        candidates.append(sub)

    found = False
    for cand in candidates:
        proj = cand.get("projection")
        if isinstance(proj, dict) and proj.get("type") == "naturalEarth1":
            found = True
            break
    assert found, (
        "Expected projection.type == 'naturalEarth1' on the layered chart or "
        "an enclosing chart spec."
    )


def _binding_range_param(spec):
    params = spec.get("params") or []
    for p in params:
        bind = p.get("bind") if isinstance(p, dict) else None
        if not isinstance(bind, dict):
            continue
        if bind.get("input") != "range":
            continue
        if (
            bind.get("min") == 1955
            and bind.get("max") == 2005
            and bind.get("step") == 5
        ):
            return p
    return None


def test_year_slider_param_present(spec):
    param = _binding_range_param(spec)
    assert param is not None, (
        "Top-level `params` must contain an entry whose `bind` is a "
        "binding_range with min=1955, max=2005, step=5."
    )
    assert isinstance(param.get("name"), str) and param["name"], (
        "The year slider parameter must have a `name`."
    )


def _collect_transforms(spec):
    out = []
    for sub in _iter_subspecs(spec):
        transforms = sub.get("transform")
        if isinstance(transforms, list):
            out.extend(transforms)
    return out


def test_transform_filter_references_year_param(spec):
    param = _binding_range_param(spec)
    assert param is not None, "Year slider parameter missing (see prior test)."
    param_name = param["name"]
    transforms = _collect_transforms(spec)
    filters = [t for t in transforms if isinstance(t, dict) and "filter" in t]
    assert filters, "Spec must contain at least one transform_filter step."

    def _filter_text(flt):
        # Vega-Lite filter can be a string expression OR a predicate object.
        if isinstance(flt, str):
            return flt
        if isinstance(flt, dict):
            return json.dumps(flt)
        return ""

    matched = False
    for t in filters:
        text = _filter_text(t["filter"])
        if param_name in text and "year" in text:
            matched = True
            break
    assert matched, (
        f"Expected a transform_filter that references both the year parameter "
        f"`{param_name}` and the `year` field. Found filters: {filters}"
    )


def test_size_encoding_has_explicit_scale_domain(spec):
    _, _, circle = _find_layered_geoshape_and_circle(spec)
    assert circle is not None, "Could not locate the circle bubble layer."
    encoding = circle.get("encoding") or {}
    size = encoding.get("size")
    assert isinstance(size, dict), (
        "The bubble layer's `size` encoding must be an object with an explicit "
        "scale."
    )
    scale = size.get("scale")
    assert isinstance(scale, dict), (
        "Size encoding must declare a `scale` object with a fixed `domain`."
    )
    domain = scale.get("domain")
    assert isinstance(domain, list) and len(domain) == 2, (
        f"Size scale `domain` must be a 2-element list, got: {domain!r}"
    )
    assert domain[0] == 0, (
        f"Size scale domain must start at 0, got first element: {domain[0]!r}"
    )
    assert isinstance(domain[1], (int, float)) and domain[1] > 0, (
        f"Size scale domain upper bound must be a positive number, got: "
        f"{domain[1]!r}"
    )


# ---------------------------------------------------------------------------
# HTML / browser verification
# ---------------------------------------------------------------------------

def test_html_contains_range_input(chart_html_text):
    # Vega embeds the binding_range as a real <input type="range"> element.
    assert re.search(
        r"<input[^>]*type=[\"']range[\"'][^>]*>", chart_html_text, re.IGNORECASE
    ) or "binding_range" in chart_html_text or '"input": "range"' in chart_html_text, (
        "Generated HTML does not appear to include a year slider widget."
    )


def test_browser_renders_map_and_slider(build_outputs):
    verifier = PochiVerifier()
    reason = (
        "The HTML chart must display a world map with bubble overlays driven "
        "by a year slider. The base layer should show country borders, the "
        "overlay should show population circles for the selected year, and a "
        "range slider labelled 'Year' (1955-2005, step 5) should control "
        "which year is displayed."
    )
    truth = (
        f"Open the local file {CHART_HTML} in a headless browser. Wait for "
        "the Vega-Lite visualization to finish rendering. Then verify all of "
        "the following:\n"
        "1. The page renders an <svg> element produced by Vega-Lite that "
        "contains many <path> elements forming country shapes (the geoshape "
        "base layer).\n"
        "2. The same <svg> contains at least one rendered circle mark from "
        "the bubble overlay (either an SVG <circle> element or a <path> "
        "rendered by Vega-Lite's circle mark).\n"
        "3. The page contains an <input> element with type='range', min='1955', "
        "max='2005', and step='5'. Moving the slider should change which "
        "bubbles are visible."
    )
    result = verifier.verify(
        reason=reason,
        truth=truth,
        use_browser_agent=True,
        trajectory_dir="/logs/verifier/pochi/test_browser_renders_map_and_slider",
    )
    assert result.status == "pass", (
        f"Browser verification failed: {getattr(result, 'reason', result)}"
    )
