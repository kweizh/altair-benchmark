import json
import os
import re
import socket
import subprocess
from typing import Any

import pytest
from xprocess import ProcessStarter

from pochi_verifier import PochiVerifier

PROJECT_DIR = "/home/user/myproject"
CHART_HTML = os.path.join(PROJECT_DIR, "chart.html")
BUILD_SCRIPT = os.path.join(PROJECT_DIR, "build_chart.py")
PREVIEW_PORT = 8765


def _extract_vega_lite_spec(html: str) -> dict[str, Any]:
    """Extract the embedded Vega-Lite JSON spec from an Altair-generated HTML file."""
    # Most common Altair template: `var spec = { ... };`
    m = re.search(r"var\s+spec\s*=\s*(\{.*?\})\s*;\s*var\s+embedOpt", html, re.DOTALL)
    if m is None:
        # Fallback: spec passed directly to vegaEmbed.
        m = re.search(
            r"vegaEmbed\(\s*[\"'][^\"']+[\"']\s*,\s*(\{.*?\})\s*[,)]",
            html,
            re.DOTALL,
        )
    if m is None:
        # Fallback: <script type="application/json"> block.
        m = re.search(
            r"<script[^>]*type=[\"']application/json[\"'][^>]*>(\{.*?\})</script>",
            html,
            re.DOTALL,
        )
    assert m is not None, (
        "Could not find an embedded Vega-Lite JSON spec inside chart.html. "
        "Expected an Altair-style `var spec = {...};` block or a vegaEmbed(...) call."
    )
    raw = m.group(1)
    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:  # pragma: no cover
        raise AssertionError(
            f"Embedded Vega-Lite spec is not valid JSON: {exc}"
        )


def _mark_type(layer: dict[str, Any]) -> str:
    mark = layer.get("mark")
    if isinstance(mark, str):
        return mark
    if isinstance(mark, dict):
        return str(mark.get("type", ""))
    return ""


def _find_layer_by_mark(spec: dict[str, Any], mark_name: str) -> dict[str, Any] | None:
    for layer in spec.get("layer", []) or []:
        if isinstance(layer, dict) and _mark_type(layer) == mark_name:
            return layer
    return None


def _collect_param_names(spec: dict[str, Any]) -> list[str]:
    names: list[str] = []
    for p in spec.get("params") or []:
        if isinstance(p, dict) and isinstance(p.get("name"), str):
            names.append(p["name"])
    for layer in spec.get("layer", []) or []:
        if not isinstance(layer, dict):
            continue
        for p in layer.get("params") or []:
            if isinstance(p, dict) and isinstance(p.get("name"), str):
                names.append(p["name"])
    return names


@pytest.fixture(scope="session")
def vega_spec() -> dict[str, Any]:
    assert os.path.isfile(CHART_HTML), (
        f"Expected the executor to produce {CHART_HTML} after running build_chart.py."
    )
    with open(CHART_HTML, "r", encoding="utf-8") as f:
        html = f.read()
    assert len(html) > 0, f"{CHART_HTML} is empty."
    return _extract_vega_lite_spec(html)


def test_chart_html_exists():
    assert os.path.isfile(BUILD_SCRIPT), (
        f"Expected build script {BUILD_SCRIPT} to exist."
    )
    assert os.path.isfile(CHART_HTML), (
        f"Expected {CHART_HTML} to be produced by `python3 build_chart.py`."
    )
    assert os.path.getsize(CHART_HTML) > 0, f"{CHART_HTML} is empty."


def test_spec_is_layered(vega_spec):
    layers = vega_spec.get("layer")
    assert isinstance(layers, list), (
        "Top-level Vega-Lite spec must contain a `layer` array (this is a layered chart)."
    )
    assert len(layers) >= 2, (
        f"Expected at least 2 layers in the layered chart, found {len(layers)}."
    )


def test_hover_selection_param(vega_spec):
    """Exactly one point selection with nearest=True, empty=False, on contains pointerover/mouseover."""
    # Collect params from top-level and from layers.
    all_params: list[dict[str, Any]] = []
    if isinstance(vega_spec.get("params"), list):
        all_params.extend([p for p in vega_spec["params"] if isinstance(p, dict)])
    for layer in vega_spec.get("layer", []) or []:
        if isinstance(layer, dict) and isinstance(layer.get("params"), list):
            all_params.extend([p for p in layer["params"] if isinstance(p, dict)])

    point_params = []
    for p in all_params:
        sel = p.get("select")
        if isinstance(sel, dict) and sel.get("type") == "point":
            point_params.append(sel)
        elif isinstance(sel, str) and sel == "point":
            point_params.append({"type": "point"})

    assert len(point_params) == 1, (
        f"Expected exactly one point selection parameter, found {len(point_params)}."
    )
    sel = point_params[0]
    assert sel.get("nearest") is True, (
        "Expected the point selection to set `nearest: true`."
    )
    assert sel.get("empty") is False, (
        "Expected the point selection to set `empty: false`."
    )
    on_event = str(sel.get("on", ""))
    assert ("pointerover" in on_event) or ("mouseover" in on_event), (
        f"Expected the point selection's `on` to contain `pointerover` or `mouseover`, "
        f"got `{on_event}`."
    )


def test_point_layer_color_condition(vega_spec):
    """Point layer color uses condition referencing the hover param: then Origin, else lightgray."""
    point_layer = _find_layer_by_mark(vega_spec, "point")
    assert point_layer is not None, (
        "Expected a layer with mark type `point` in the layered chart."
    )
    encoding = point_layer.get("encoding") or {}
    color = encoding.get("color")
    assert isinstance(color, dict), (
        f"Expected `encoding.color` on the point layer to be a dict, got {type(color).__name__}."
    )
    condition = color.get("condition")
    assert condition is not None, (
        "Expected `encoding.color` to use a `condition` keyed on the hover selection."
    )
    # condition may be a dict or list of dicts; normalize to list for inspection.
    conditions = condition if isinstance(condition, list) else [condition]
    matched_origin = False
    param_names = _collect_param_names(vega_spec)
    for cond in conditions:
        if not isinstance(cond, dict):
            continue
        # Must reference the hover param (by name or via test).
        refs_param = (
            isinstance(cond.get("param"), str) and cond["param"] in param_names
        ) or ("test" in cond)
        if refs_param and cond.get("field") == "Origin":
            matched_origin = True
            break
    assert matched_origin, (
        "Expected the point layer's color condition to reference the hover param "
        "and resolve to field `Origin` when active."
    )
    # Fallback (else branch) must be lightgray (value).
    assert color.get("value") == "lightgray", (
        f"Expected `encoding.color.value` (the otherwise branch) to be 'lightgray', "
        f"got {color.get('value')!r}."
    )


def test_text_layer_encoding(vega_spec):
    """Text layer: mark.dy == -10, text.field == 'Name', opacity condition then=1 else=0."""
    text_layer = _find_layer_by_mark(vega_spec, "text")
    assert text_layer is not None, (
        "Expected a layer with mark type `text` in the layered chart."
    )
    mark = text_layer.get("mark")
    assert isinstance(mark, dict), (
        "Expected the text layer's `mark` to be an object (so it can carry `dy`)."
    )
    assert mark.get("dy") == -10, (
        f"Expected the text layer's `mark.dy` to be -10, got {mark.get('dy')!r}."
    )

    encoding = text_layer.get("encoding") or {}
    text_enc = encoding.get("text")
    assert isinstance(text_enc, dict), (
        f"Expected `encoding.text` on the text layer to be a dict, got {type(text_enc).__name__}."
    )
    assert text_enc.get("field") == "Name", (
        f"Expected `encoding.text.field` to be 'Name', got {text_enc.get('field')!r}."
    )

    opacity = encoding.get("opacity")
    assert isinstance(opacity, dict), (
        f"Expected `encoding.opacity` on the text layer to be a dict, got {type(opacity).__name__}."
    )
    condition = opacity.get("condition")
    assert condition is not None, (
        "Expected `encoding.opacity` to use a `condition` keyed on the hover selection."
    )
    conditions = condition if isinstance(condition, list) else [condition]
    param_names = _collect_param_names(vega_spec)
    matched_then = False
    for cond in conditions:
        if not isinstance(cond, dict):
            continue
        refs_param = (
            isinstance(cond.get("param"), str) and cond["param"] in param_names
        ) or ("test" in cond)
        if refs_param and cond.get("value") == 1:
            matched_then = True
            break
    assert matched_then, (
        "Expected the text layer's opacity condition to reference the hover param "
        "and resolve to value 1 when active."
    )
    assert opacity.get("value") == 0, (
        f"Expected `encoding.opacity.value` (the otherwise branch) to be 0, "
        f"got {opacity.get('value')!r}."
    )


def test_axes_scale_zero_false(vega_spec):
    """Both x and y encodings (in at least one layer each) must have scale.zero == false."""
    layers = vega_spec.get("layer", []) or []
    found_x = False
    found_y = False
    for layer in layers:
        if not isinstance(layer, dict):
            continue
        encoding = layer.get("encoding") or {}
        x_enc = encoding.get("x")
        if isinstance(x_enc, dict):
            scale = x_enc.get("scale") or {}
            if isinstance(scale, dict) and scale.get("zero") is False:
                found_x = True
        y_enc = encoding.get("y")
        if isinstance(y_enc, dict):
            scale = y_enc.get("scale") or {}
            if isinstance(scale, dict) and scale.get("zero") is False:
                found_y = True
    assert found_x, (
        "Expected at least one layer whose `encoding.x.scale.zero` is `false`."
    )
    assert found_y, (
        "Expected at least one layer whose `encoding.y.scale.zero` is `false`."
    )


def test_spec_width_height(vega_spec):
    assert vega_spec.get("width") == 600, (
        f"Expected top-level `width` to be 600, got {vega_spec.get('width')!r}."
    )
    assert vega_spec.get("height") == 400, (
        f"Expected top-level `height` to be 400, got {vega_spec.get('height')!r}."
    )


@pytest.fixture(scope="session")
def chart_preview_server(xprocess):
    """Serve the project directory over HTTP so a headless browser can load chart.html."""

    class Starter(ProcessStarter):
        name = "altair_chart_preview"
        args = ["python3", "-m", "http.server", str(PREVIEW_PORT)]
        env = os.environ.copy()
        popen_kwargs = {
            "cwd": PROJECT_DIR,
            "text": True,
        }
        timeout = 60
        terminate_on_interrupt = True

        def startup_check(self):
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                return s.connect_ex(("localhost", PREVIEW_PORT)) == 0

    xprocess.ensure(Starter.name, Starter)
    yield f"http://localhost:{PREVIEW_PORT}/chart.html"
    info = xprocess.getinfo(Starter.name)
    info.terminate()


def test_browser_hover_highlight(chart_preview_server):
    reason = (
        "The Altair-generated chart.html must render a scatter plot of the cars dataset where "
        "all points appear in light gray by default. When the pointer hovers over a point area, "
        "the nearest point must change color (matching its Origin category) AND a text label "
        "showing the car's Name must appear above it. The hover state must disappear when the "
        "pointer leaves the chart, and the page must produce no JavaScript console errors."
    )
    truth = (
        f"Navigate to {chart_preview_server} in a browser. "
        "Wait for the Vega-Lite chart to finish rendering. "
        "1) Verify that the page has no JavaScript console errors. "
        "2) Verify the rendered chart shows a scatter plot of points where most/all points are "
        "rendered in light gray when the pointer is NOT over any point (e.g., when the pointer "
        "is outside the plotting area). No car-name text labels should be visible in this state. "
        "3) Move the pointer onto the plot area and place it directly over a visible point (for "
        "example, near the middle of the scatter cloud where points are dense). Verify that "
        "the nearest point's color changes from light gray to a non-gray color corresponding to "
        "its Origin category (e.g., a red/blue/orange Vega category color) AND a text label "
        "showing the car's Name appears next to (above) that point. "
        "4) Move the pointer to a different point and verify the highlight + Name label follow "
        "the nearest point. "
        "5) Move the pointer off the chart and verify the highlight and the Name label disappear "
        "(points return to light gray)."
    )
    verifier = PochiVerifier()
    result = verifier.verify(
        reason=reason,
        truth=truth,
        use_browser_agent=True,
        trajectory_dir="/logs/verifier/pochi/test_browser_hover_highlight",
    )
    assert result.status == "pass", f"Browser verification failed: {result.reason}"


def test_build_script_is_idempotent():
    """Sanity check: the executor's build script should be re-runnable."""
    result = subprocess.run(
        ["python3", "build_chart.py"],
        capture_output=True,
        text=True,
        cwd=PROJECT_DIR,
    )
    assert result.returncode == 0, (
        f"`python3 build_chart.py` failed on re-run.\nstdout: {result.stdout}\nstderr: {result.stderr}"
    )
    assert os.path.isfile(CHART_HTML), (
        f"{CHART_HTML} should still exist after re-running build_chart.py."
    )
