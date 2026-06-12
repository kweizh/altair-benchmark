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


def _iter_marks(layer: dict[str, Any]) -> str:
    mark = layer.get("mark")
    if isinstance(mark, str):
        return mark
    if isinstance(mark, dict):
        return str(mark.get("type", ""))
    return ""


def _collect_transforms(spec: dict[str, Any]) -> list[dict[str, Any]]:
    transforms: list[dict[str, Any]] = []
    if isinstance(spec.get("transform"), list):
        transforms.extend(spec["transform"])
    for layer in spec.get("layer", []) or []:
        if isinstance(layer, dict) and isinstance(layer.get("transform"), list):
            transforms.extend(layer["transform"])
    return transforms


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


def test_spec_is_layered_with_at_least_five_layers(vega_spec):
    layers = vega_spec.get("layer")
    assert isinstance(layers, list), (
        "Top-level Vega-Lite spec must contain a `layer` array (this is a layered chart)."
    )
    assert len(layers) >= 5, (
        f"Expected at least 5 layers in the layered chart, found {len(layers)}."
    )


def test_required_mark_types_present(vega_spec):
    layers = vega_spec.get("layer", []) or []
    mark_types = {_iter_marks(layer) for layer in layers if isinstance(layer, dict)}
    for required in ("area", "line", "bar", "rule", "text"):
        assert required in mark_types, (
            f"Expected a layer with mark type `{required}`. "
            f"Found mark types: {sorted(mark_types)}."
        )


def test_area_layer_has_y_and_y2(vega_spec):
    found = False
    for layer in vega_spec.get("layer", []) or []:
        if not isinstance(layer, dict):
            continue
        if _iter_marks(layer) != "area":
            continue
        encoding = layer.get("encoding") or {}
        if "y" in encoding and "y2" in encoding:
            found = True
            break
    assert found, (
        "Expected at least one `area` layer that encodes both `y` and `y2` "
        "to draw the daily temp_min->temp_max range."
    )


def test_zero_degree_rule_annotation(vega_spec):
    found = False
    for layer in vega_spec.get("layer", []) or []:
        if not isinstance(layer, dict):
            continue
        if _iter_marks(layer) != "rule":
            continue
        encoding = layer.get("encoding") or {}
        y = encoding.get("y")
        if isinstance(y, dict) and y.get("datum") == 0:
            found = True
            break
    assert found, (
        "Expected a `rule` layer encoded at the data value y=0 "
        "(the dashed 0-degree annotation)."
    )


def test_transform_calculate_for_mean_temperature(vega_spec):
    transforms = _collect_transforms(vega_spec)
    calc_transforms = [t for t in transforms if isinstance(t, dict) and "calculate" in t]
    assert calc_transforms, (
        "Expected at least one `transform_calculate` entry that derives the mean temperature."
    )
    matched = False
    for t in calc_transforms:
        expr = str(t.get("calculate", ""))
        if "temp_min" in expr and "temp_max" in expr:
            matched = True
            break
    assert matched, (
        "Expected a calculate transform whose expression references both "
        "`temp_min` and `temp_max` (the mean temperature derivation)."
    )


def test_resolve_scale_y_independent(vega_spec):
    resolve = vega_spec.get("resolve") or {}
    scale = resolve.get("scale") or {}
    assert scale.get("y") == "independent", (
        "Expected top-level `resolve.scale.y` to be `\"independent\"` so the "
        "precipitation bars can use a secondary y axis."
    )


def test_nearest_x_hover_selection_param(vega_spec):
    params = vega_spec.get("params") or []
    assert isinstance(params, list) and len(params) >= 1, (
        "Expected the spec to declare at least one selection parameter."
    )
    point_params = []
    for p in params:
        if not isinstance(p, dict):
            continue
        sel = p.get("select")
        if isinstance(sel, dict) and sel.get("type") == "point":
            point_params.append(sel)
    assert len(point_params) == 1, (
        f"Expected exactly one point selection parameter, found {len(point_params)}."
    )
    sel = point_params[0]
    assert sel.get("nearest") is True, (
        "Expected the point selection to set `nearest: true`."
    )
    encodings = sel.get("encodings") or []
    assert "x" in encodings, (
        f"Expected the point selection's `encodings` to include `x`, got {encodings}."
    )
    assert sel.get("empty") is False, (
        "Expected the point selection to set `empty: false`."
    )
    on_event = str(sel.get("on", ""))
    assert ("pointerover" in on_event) or ("mouseover" in on_event), (
        f"Expected the point selection's `on` to contain `pointerover` or `mouseover`, got `{on_event}`."
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


def test_browser_renders_all_layers(chart_preview_server):
    reason = (
        "The Altair-generated chart.html must render a layered Seattle weather chart that visibly "
        "combines (1) a pale-orange temperature-range area, (2) a mean-temperature line, "
        "(3) precipitation bars on a secondary y axis, (4) a dashed annotation rule at 0 degrees C, "
        "and (5) a hover-driven nearest-x tooltip layer with a vertical rule and text."
    )
    truth = (
        f"Navigate to {chart_preview_server} in a browser. "
        "Wait for the Vega-Lite chart to finish rendering. "
        "Verify that the page has no JavaScript console errors and that the rendered chart contains "
        "all of the following visible marks: a filled area band spanning daily min/max temperatures, "
        "a line connecting daily mean temperatures, vertical bars representing daily precipitation, "
        "a dashed horizontal rule at the 0 degree mark, and at least one text label "
        "(the tooltip layer rendering date / mean temperature / precipitation). "
        "Then move the pointer over the chart area and verify that a hover state activates "
        "(a vertical rule and tooltip text appear or update) without errors."
    )
    verifier = PochiVerifier()
    result = verifier.verify(
        reason=reason,
        truth=truth,
        use_browser_agent=True,
        trajectory_dir="/logs/verifier/pochi/test_browser_renders_all_layers",
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
