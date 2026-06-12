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


def test_mark_is_bar(vega_spec):
    mark = _mark_type(vega_spec)
    assert mark == "bar", (
        f"Expected the top-level chart `mark` to be `bar`, got `{mark}`."
    )


def test_y_encoding_site_with_aggregate_sort(vega_spec):
    encoding = vega_spec.get("encoding") or {}
    y = encoding.get("y")
    assert isinstance(y, dict), (
        f"Expected `encoding.y` to be an object, got: {y!r}."
    )
    assert y.get("field") == "site", (
        f"Expected `encoding.y.field` to be `site`, got `{y.get('field')!r}`."
    )
    assert y.get("type") == "nominal", (
        f"Expected `encoding.y.type` to be `nominal`, got `{y.get('type')!r}`."
    )
    sort = y.get("sort")
    assert isinstance(sort, dict), (
        f"Expected `encoding.y.sort` to be an object with field/op/order; got: {sort!r}. "
        "Use Altair's `sort(field='yield', op='mean', order='descending')` aggregation-based sort."
    )
    assert sort.get("field") == "yield", (
        f"Expected `encoding.y.sort.field` to be `yield`, got `{sort.get('field')!r}`."
    )
    assert sort.get("op") == "mean", (
        f"Expected `encoding.y.sort.op` to be `mean`, got `{sort.get('op')!r}`."
    )
    assert sort.get("order") == "descending", (
        f"Expected `encoding.y.sort.order` to be `descending`, got `{sort.get('order')!r}`."
    )


def test_x_encoding_mean_yield_quantitative(vega_spec):
    encoding = vega_spec.get("encoding") or {}
    x = encoding.get("x")
    assert isinstance(x, dict), (
        f"Expected `encoding.x` to be an object, got: {x!r}."
    )
    assert x.get("field") == "yield", (
        f"Expected `encoding.x.field` to be `yield`, got `{x.get('field')!r}`."
    )
    assert x.get("aggregate") == "mean", (
        f"Expected `encoding.x.aggregate` to be `mean`, got `{x.get('aggregate')!r}`."
    )
    assert x.get("type") == "quantitative", (
        f"Expected `encoding.x.type` to be `quantitative`, got `{x.get('type')!r}`."
    )


def test_color_encoding_year_nominal(vega_spec):
    encoding = vega_spec.get("encoding") or {}
    color = encoding.get("color")
    assert isinstance(color, dict), (
        f"Expected `encoding.color` to be an object, got: {color!r}."
    )
    assert color.get("field") == "year", (
        f"Expected `encoding.color.field` to be `year`, got `{color.get('field')!r}`."
    )
    assert color.get("type") == "nominal", (
        f"Expected `encoding.color.type` to be `nominal`, got `{color.get('type')!r}`."
    )


def test_yoffset_encoding_year_nominal(vega_spec):
    encoding = vega_spec.get("encoding") or {}
    yoffset = encoding.get("yOffset")
    assert isinstance(yoffset, dict), (
        f"Expected `encoding.yOffset` to be an object (the grouping channel), got: {yoffset!r}."
    )
    assert yoffset.get("field") == "year", (
        f"Expected `encoding.yOffset.field` to be `year`, got `{yoffset.get('field')!r}`."
    )
    assert yoffset.get("type") == "nominal", (
        f"Expected `encoding.yOffset.type` to be `nominal`, got `{yoffset.get('type')!r}`."
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


def test_browser_renders_grouped_bars(chart_preview_server):
    reason = (
        "The Altair-generated chart.html must render a horizontal grouped bar chart of the barley "
        "dataset: each site is a row on the y axis (sorted from highest to lowest mean yield), "
        "and within each row the bars for different years sit side-by-side (grouped via yOffset, "
        "NOT stacked). The chart must include a legend mapping year values to distinct colors."
    )
    truth = (
        f"Navigate to {chart_preview_server} in a browser. "
        "Wait for the Vega-Lite chart to finish rendering. "
        "Verify that the page has no JavaScript console errors. "
        "Verify that the rendered chart is a HORIZONTAL bar chart: bars extend along the x axis, "
        "and the y axis lists site names (e.g., values such as 'University Farm', 'Waseca', "
        "'Morris', 'Crookston', 'Grand Rapids', 'Duluth'). "
        "Verify that within each site row there are at least 2 adjacent (grouped, NOT stacked) "
        "bars representing different years, so bars of different colors are placed side-by-side "
        "vertically within the same site band rather than being drawn on top of each other. "
        "Verify that a color legend is visible and that it maps year values to at least two "
        "distinct colored swatches. "
        "Verify that the sites are ordered from highest mean yield at the top to lowest mean "
        "yield at the bottom (descending sort by mean yield)."
    )
    verifier = PochiVerifier()
    result = verifier.verify(
        reason=reason,
        truth=truth,
        use_browser_agent=True,
        trajectory_dir="/logs/verifier/pochi/test_browser_renders_grouped_bars",
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
