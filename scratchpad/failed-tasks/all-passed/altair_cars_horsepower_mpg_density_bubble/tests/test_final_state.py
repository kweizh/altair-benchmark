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


def _mark_type(spec: dict[str, Any]) -> str:
    mark = spec.get("mark")
    if isinstance(mark, str):
        return mark
    if isinstance(mark, dict):
        return str(mark.get("type", ""))
    return ""


def _title_text(spec: dict[str, Any]) -> str:
    title = spec.get("title")
    if isinstance(title, str):
        return title
    if isinstance(title, dict):
        text = title.get("text")
        if isinstance(text, str):
            return text
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


def test_spec_is_not_layered(vega_spec):
    assert "layer" not in vega_spec, (
        "Expected a single (non-layered) chart, but the spec contains a top-level `layer` array."
    )


def test_mark_is_circle(vega_spec):
    mark_type = _mark_type(vega_spec)
    assert mark_type == "circle", (
        f"Expected `mark` type to be `circle`, got `{mark_type!r}`."
    )


def test_x_encoding_horsepower_binned(vega_spec):
    encoding = vega_spec.get("encoding") or {}
    x = encoding.get("x")
    assert isinstance(x, dict), (
        "Expected `encoding.x` to be an object describing the Horsepower binned field."
    )
    assert x.get("field") == "Horsepower", (
        f"Expected `encoding.x.field == 'Horsepower'`, got {x.get('field')!r}."
    )
    bin_spec = x.get("bin")
    assert isinstance(bin_spec, dict), (
        f"Expected `encoding.x.bin` to be an object like {{'maxbins': 10}}, got {bin_spec!r}."
    )
    assert bin_spec.get("maxbins") == 10, (
        f"Expected `encoding.x.bin.maxbins == 10`, got {bin_spec.get('maxbins')!r}."
    )


def test_y_encoding_mpg_binned(vega_spec):
    encoding = vega_spec.get("encoding") or {}
    y = encoding.get("y")
    assert isinstance(y, dict), (
        "Expected `encoding.y` to be an object describing the Miles_per_Gallon binned field."
    )
    assert y.get("field") == "Miles_per_Gallon", (
        f"Expected `encoding.y.field == 'Miles_per_Gallon'`, got {y.get('field')!r}."
    )
    bin_spec = y.get("bin")
    assert isinstance(bin_spec, dict), (
        f"Expected `encoding.y.bin` to be an object like {{'maxbins': 10}}, got {bin_spec!r}."
    )
    assert bin_spec.get("maxbins") == 10, (
        f"Expected `encoding.y.bin.maxbins == 10`, got {bin_spec.get('maxbins')!r}."
    )


def test_size_encoding_count_aggregate(vega_spec):
    encoding = vega_spec.get("encoding") or {}
    size = encoding.get("size")
    assert isinstance(size, dict), (
        "Expected `encoding.size` to be an object encoding count() per bin."
    )
    assert size.get("aggregate") == "count", (
        f"Expected `encoding.size.aggregate == 'count'`, got {size.get('aggregate')!r}."
    )


def test_color_encoding_mean_acceleration_viridis(vega_spec):
    encoding = vega_spec.get("encoding") or {}
    color = encoding.get("color")
    assert isinstance(color, dict), (
        "Expected `encoding.color` to be an object encoding mean(Acceleration) with a viridis scheme."
    )
    assert color.get("aggregate") == "mean", (
        f"Expected `encoding.color.aggregate == 'mean'`, got {color.get('aggregate')!r}."
    )
    assert color.get("field") == "Acceleration", (
        f"Expected `encoding.color.field == 'Acceleration'`, got {color.get('field')!r}."
    )
    scale = color.get("scale")
    assert isinstance(scale, dict), (
        f"Expected `encoding.color.scale` to be an object with `scheme: 'viridis'`, got {scale!r}."
    )
    assert scale.get("scheme") == "viridis", (
        f"Expected `encoding.color.scale.scheme == 'viridis'`, got {scale.get('scheme')!r}."
    )


def test_chart_properties_width_height_title(vega_spec):
    assert vega_spec.get("width") == 400, (
        f"Expected top-level `width == 400`, got {vega_spec.get('width')!r}."
    )
    assert vega_spec.get("height") == 300, (
        f"Expected top-level `height == 300`, got {vega_spec.get('height')!r}."
    )
    title = _title_text(vega_spec)
    assert title == "Cars Horsepower vs MPG Density", (
        f"Expected chart title to be 'Cars Horsepower vs MPG Density', got {title!r}."
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


def test_browser_renders_bubble_density(chart_preview_server):
    reason = (
        "The Altair-generated chart.html must render a 2D binned bubble density plot of the cars dataset. "
        "Horsepower is on the x-axis and Miles_per_Gallon is on the y-axis, both binned into at most 10 bins, "
        "so bubbles appear arranged roughly in a grid. The bubble size encodes the count of cars in each bin, "
        "and the bubble color encodes the mean Acceleration on a viridis color scheme. A color legend showing the "
        "viridis ramp must be visible, and the chart must be titled 'Cars Horsepower vs MPG Density'."
    )
    truth = (
        f"Navigate to {chart_preview_server} in a browser. "
        "Wait for the Vega-Lite chart to finish rendering. "
        "Verify that the page has no JavaScript console errors. "
        "Verify that the rendered chart contains multiple circle bubbles of clearly varying sizes arranged roughly "
        "in a grid pattern (because both x and y axes are binned). "
        "Verify that the bubble colors use a viridis-like ramp (typically yellow/green/teal/blue/purple), and that "
        "a color legend with a continuous viridis-like ramp labeled for `mean(Acceleration)` (or `Acceleration`) is visible. "
        "Verify that the chart title 'Cars Horsepower vs MPG Density' is visible somewhere on the chart."
    )
    verifier = PochiVerifier()
    result = verifier.verify(
        reason=reason,
        truth=truth,
        use_browser_agent=True,
        trajectory_dir="/logs/verifier/pochi/test_browser_renders_bubble_density",
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
