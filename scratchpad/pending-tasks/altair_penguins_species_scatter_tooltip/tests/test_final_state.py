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

EXPECTED_TOOLTIP_FIELDS = [
    "Species",
    "Island",
    "Flipper Length (mm)",
    "Body Mass (g)",
]


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


def _tooltip_field_name(entry: Any) -> str:
    """Normalize a tooltip-list entry to its field name string."""
    if isinstance(entry, str):
        # Shorthand syntax: "Species:N" -> "Species"
        return entry.split(":")[0].strip()
    if isinstance(entry, dict):
        return str(entry.get("field", ""))
    return ""


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


def test_mark_is_filled_point_with_size_80(vega_spec):
    mark = vega_spec.get("mark")
    assert isinstance(mark, dict), (
        f"Expected `mark` to be an object with `type`, `filled`, and `size` properties, got: {mark!r}"
    )
    assert mark.get("type") == "point", (
        f"Expected `mark.type` == 'point', got {mark.get('type')!r}"
    )
    assert mark.get("filled") is True, (
        f"Expected `mark.filled` to be true, got {mark.get('filled')!r}"
    )
    assert mark.get("size") == 80, (
        f"Expected `mark.size` to be 80, got {mark.get('size')!r}"
    )


def test_x_encoding_flipper_length_scale_zero_false(vega_spec):
    encoding = vega_spec.get("encoding") or {}
    x = encoding.get("x")
    assert isinstance(x, dict), (
        f"Expected `encoding.x` to be an object, got: {x!r}"
    )
    assert x.get("field") == "Flipper Length (mm)", (
        f"Expected `encoding.x.field` == 'Flipper Length (mm)', got {x.get('field')!r}"
    )
    assert x.get("type") == "quantitative", (
        f"Expected `encoding.x.type` == 'quantitative', got {x.get('type')!r}"
    )
    scale = x.get("scale") or {}
    assert scale.get("zero") is False, (
        f"Expected `encoding.x.scale.zero` == false, got {scale.get('zero')!r}"
    )


def test_y_encoding_body_mass_scale_zero_false(vega_spec):
    encoding = vega_spec.get("encoding") or {}
    y = encoding.get("y")
    assert isinstance(y, dict), (
        f"Expected `encoding.y` to be an object, got: {y!r}"
    )
    assert y.get("field") == "Body Mass (g)", (
        f"Expected `encoding.y.field` == 'Body Mass (g)', got {y.get('field')!r}"
    )
    assert y.get("type") == "quantitative", (
        f"Expected `encoding.y.type` == 'quantitative', got {y.get('type')!r}"
    )
    scale = y.get("scale") or {}
    assert scale.get("zero") is False, (
        f"Expected `encoding.y.scale.zero` == false, got {scale.get('zero')!r}"
    )


def test_color_encoding_species_nominal(vega_spec):
    encoding = vega_spec.get("encoding") or {}
    color = encoding.get("color")
    assert isinstance(color, dict), (
        f"Expected `encoding.color` to be an object, got: {color!r}"
    )
    assert color.get("field") == "Species", (
        f"Expected `encoding.color.field` == 'Species', got {color.get('field')!r}"
    )
    assert color.get("type") == "nominal", (
        f"Expected `encoding.color.type` == 'nominal', got {color.get('type')!r}"
    )


def test_shape_encoding_sex_nominal(vega_spec):
    encoding = vega_spec.get("encoding") or {}
    shape = encoding.get("shape")
    assert isinstance(shape, dict), (
        f"Expected `encoding.shape` to be an object, got: {shape!r}"
    )
    assert shape.get("field") == "Sex", (
        f"Expected `encoding.shape.field` == 'Sex', got {shape.get('field')!r}"
    )
    assert shape.get("type") == "nominal", (
        f"Expected `encoding.shape.type` == 'nominal', got {shape.get('type')!r}"
    )


def test_tooltip_encoding_has_all_four_fields_in_order(vega_spec):
    encoding = vega_spec.get("encoding") or {}
    tooltip = encoding.get("tooltip")
    assert isinstance(tooltip, list), (
        f"Expected `encoding.tooltip` to be a list, got: {type(tooltip).__name__}"
    )
    assert len(tooltip) == 4, (
        f"Expected `encoding.tooltip` to have exactly 4 entries, got {len(tooltip)}"
    )
    actual_fields = [_tooltip_field_name(entry) for entry in tooltip]
    assert actual_fields == EXPECTED_TOOLTIP_FIELDS, (
        f"Expected tooltip fields {EXPECTED_TOOLTIP_FIELDS} in order, got {actual_fields}"
    )


def test_interactive_interval_selection_bound_to_scales(vega_spec):
    params = vega_spec.get("params") or []
    assert isinstance(params, list) and len(params) >= 1, (
        "Expected the spec to declare at least one selection parameter from `.interactive()`."
    )
    matched = False
    for p in params:
        if not isinstance(p, dict):
            continue
        sel = p.get("select")
        sel_type = None
        if isinstance(sel, dict):
            sel_type = sel.get("type")
        elif isinstance(sel, str):
            sel_type = sel
        if sel_type != "interval":
            continue
        if p.get("bind") == "scales":
            matched = True
            break
    assert matched, (
        "Expected at least one params entry with `select.type == 'interval'` "
        "and `bind == 'scales'` (the selection produced by `.interactive()`)."
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


def test_browser_renders_scatter_with_colors_shapes_and_tooltip(chart_preview_server):
    reason = (
        "The Altair-generated chart.html must render a penguins scatter plot with: "
        "(1) points visible on screen using `mark_point(filled=True, size=80)`, "
        "(2) at least 3 distinct fill colors encoding the `Species` channel "
        "(Adelie / Chinstrap / Gentoo), "
        "(3) at least 2 distinct point shapes encoding the `Sex` channel, "
        "and (4) a hover tooltip that includes the species name."
    )
    truth = (
        f"Navigate to {chart_preview_server} in a browser. "
        "Wait for the Vega-Lite scatter plot to finish rendering. "
        "Verify that the page has no JavaScript console errors and that the chart contains "
        "visible point marks. Inspect the rendered points and verify that they use at least "
        "3 distinct fill colors (one per penguin species) and at least 2 distinct point "
        "shapes (one per sex category). Then move the pointer over any point and verify that "
        "a tooltip appears whose visible text contains at least one of the species names: "
        "`Adelie`, `Chinstrap`, or `Gentoo`."
    )
    verifier = PochiVerifier()
    result = verifier.verify(
        reason=reason,
        truth=truth,
        use_browser_agent=True,
        trajectory_dir="/logs/verifier/pochi/test_browser_renders_scatter_with_colors_shapes_and_tooltip",
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
