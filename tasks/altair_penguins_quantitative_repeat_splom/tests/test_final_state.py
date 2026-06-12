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

EXPECTED_ROW = ["Body Mass (g)", "Flipper Length (mm)"]
EXPECTED_COLUMN = ["Beak Length (mm)", "Beak Depth (mm)"]


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


def _mark_type(spec: dict[str, Any]) -> str:
    mark = spec.get("mark")
    if isinstance(mark, str):
        return mark
    if isinstance(mark, dict):
        return str(mark.get("type", ""))
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


@pytest.fixture(scope="session")
def repeated_subspec(vega_spec) -> dict[str, Any]:
    subspec = vega_spec.get("spec")
    assert isinstance(subspec, dict), (
        "Top-level Vega-Lite spec must contain a `spec` object describing the repeated subspec."
    )
    return subspec


def test_chart_html_exists():
    assert os.path.isfile(BUILD_SCRIPT), (
        f"Expected build script {BUILD_SCRIPT} to exist."
    )
    assert os.path.isfile(CHART_HTML), (
        f"Expected {CHART_HTML} to be produced by `python3 build_chart.py`."
    )
    assert os.path.getsize(CHART_HTML) > 0, f"{CHART_HTML} is empty."


def test_spec_has_repeat_row_and_column(vega_spec):
    repeat = vega_spec.get("repeat")
    assert isinstance(repeat, dict), (
        "Top-level Vega-Lite spec must contain a `repeat` object with `row` and `column` arrays."
    )
    assert repeat.get("row") == EXPECTED_ROW, (
        f"Expected `repeat.row` to be {EXPECTED_ROW}, got {repeat.get('row')}."
    )
    assert repeat.get("column") == EXPECTED_COLUMN, (
        f"Expected `repeat.column` to be {EXPECTED_COLUMN}, got {repeat.get('column')}."
    )


def test_repeated_subspec_is_point(repeated_subspec):
    mark_type = _mark_type(repeated_subspec)
    assert mark_type == "point", (
        f"Expected the repeated subspec's `mark` type to be `point`, got `{mark_type}`."
    )


def test_repeated_subspec_x_encoding(repeated_subspec):
    encoding = repeated_subspec.get("encoding") or {}
    x = encoding.get("x")
    assert isinstance(x, dict), (
        "Expected the repeated subspec's encoding.x to be defined as an object."
    )
    assert x.get("field") == {"repeat": "column"}, (
        f"Expected encoding.x.field to be {{'repeat': 'column'}}, got {x.get('field')}."
    )
    assert x.get("type") == "quantitative", (
        f"Expected encoding.x.type to be 'quantitative', got {x.get('type')}."
    )


def test_repeated_subspec_y_encoding(repeated_subspec):
    encoding = repeated_subspec.get("encoding") or {}
    y = encoding.get("y")
    assert isinstance(y, dict), (
        "Expected the repeated subspec's encoding.y to be defined as an object."
    )
    assert y.get("field") == {"repeat": "row"}, (
        f"Expected encoding.y.field to be {{'repeat': 'row'}}, got {y.get('field')}."
    )
    assert y.get("type") == "quantitative", (
        f"Expected encoding.y.type to be 'quantitative', got {y.get('type')}."
    )


def test_repeated_subspec_color_encoding(repeated_subspec):
    encoding = repeated_subspec.get("encoding") or {}
    color = encoding.get("color")
    assert isinstance(color, dict), (
        "Expected the repeated subspec's encoding.color to be defined as an object."
    )
    assert color.get("field") == "Species", (
        f"Expected encoding.color.field to be 'Species', got {color.get('field')}."
    )


def test_repeated_subspec_width_and_height(repeated_subspec):
    assert repeated_subspec.get("width") == 180, (
        f"Expected the repeated subspec's width to be 180, got {repeated_subspec.get('width')}."
    )
    assert repeated_subspec.get("height") == 180, (
        f"Expected the repeated subspec's height to be 180, got {repeated_subspec.get('height')}."
    )


def test_repeated_subspec_scale_zero_false(repeated_subspec):
    encoding = repeated_subspec.get("encoding") or {}
    x_scale = (encoding.get("x") or {}).get("scale") or {}
    y_scale = (encoding.get("y") or {}).get("scale") or {}
    assert x_scale.get("zero") is False, (
        f"Expected encoding.x.scale.zero to be false, got {x_scale.get('zero')}."
    )
    assert y_scale.get("zero") is False, (
        f"Expected encoding.y.scale.zero to be false, got {y_scale.get('zero')}."
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


def test_browser_renders_splom_grid(chart_preview_server):
    reason = (
        "The Altair-generated chart.html must render a 2x2 scatter plot matrix (SPLOM) of the "
        "Palmer Penguins dataset built with `repeat`. The four panels correspond to "
        "Beak Length (mm) and Beak Depth (mm) on the x-axis (columns) crossed with "
        "Body Mass (g) and Flipper Length (mm) on the y-axis (rows). Points must be colored "
        "by Species (three distinct colors) and a single shared color legend must be visible."
    )
    truth = (
        f"Navigate to {chart_preview_server} in a browser. Wait for the Vega-Lite chart to finish "
        "rendering. Verify that the page has no JavaScript console errors and that the rendered "
        "chart contains a 2x2 grid of four scatter plots. Verify that the points in every panel "
        "are colored by Species using three distinct colors (one per species: Adelie, Chinstrap, "
        "Gentoo). Verify that exactly one shared color legend titled `Species` is rendered "
        "(typically to the right of or below the grid), not one legend per panel."
    )
    verifier = PochiVerifier()
    result = verifier.verify(
        reason=reason,
        truth=truth,
        use_browser_agent=True,
        trajectory_dir="/logs/verifier/pochi/test_browser_renders_splom_grid",
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
