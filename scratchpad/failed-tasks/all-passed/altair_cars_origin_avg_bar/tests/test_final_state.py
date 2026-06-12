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

DISALLOWED_TOP_LEVEL_COMPOSITIONS = (
    "layer",
    "concat",
    "hconcat",
    "vconcat",
    "facet",
    "repeat",
)


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


def _mark_type(mark: Any) -> str:
    if isinstance(mark, str):
        return mark
    if isinstance(mark, dict):
        return str(mark.get("type", ""))
    return ""


def _y_aggregates_mean_mpg(encoding: dict[str, Any]) -> bool:
    y = encoding.get("y")
    if not isinstance(y, dict):
        return False
    return (
        y.get("aggregate") == "mean"
        and y.get("field") == "Miles_per_Gallon"
    )


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


def test_spec_is_single_bar_chart(vega_spec):
    for key in DISALLOWED_TOP_LEVEL_COMPOSITIONS:
        assert key not in vega_spec, (
            f"Top-level Vega-Lite spec must not use `{key}` composition; "
            f"the task expects a single non-composed bar chart."
        )
    mark = vega_spec.get("mark")
    assert mark is not None, (
        "Top-level Vega-Lite spec must declare a `mark` (this is a single bar chart)."
    )
    mark_type = _mark_type(mark)
    assert mark_type == "bar", (
        f"Expected the top-level `mark` to be `bar`, got `{mark_type!r}`."
    )


def test_encoding_x_origin_nominal(vega_spec):
    encoding = vega_spec.get("encoding") or {}
    x = encoding.get("x")
    assert isinstance(x, dict), (
        "Expected `encoding.x` to be an object specifying the field and type."
    )
    assert x.get("field") == "Origin", (
        f"Expected `encoding.x.field == 'Origin'`, got {x.get('field')!r}."
    )
    assert x.get("type") == "nominal", (
        f"Expected `encoding.x.type == 'nominal'`, got {x.get('type')!r}."
    )


def test_encoding_y_aggregates_mean_mpg(vega_spec):
    encoding = vega_spec.get("encoding") or {}
    y = encoding.get("y")
    assert isinstance(y, dict), (
        "Expected `encoding.y` to be an object specifying the field, aggregate, and type."
    )
    assert y.get("field") == "Miles_per_Gallon", (
        f"Expected `encoding.y.field == 'Miles_per_Gallon'`, got {y.get('field')!r}."
    )
    assert y.get("aggregate") == "mean", (
        f"Expected `encoding.y.aggregate == 'mean'`, got {y.get('aggregate')!r}."
    )
    assert y.get("type") == "quantitative", (
        f"Expected `encoding.y.type == 'quantitative'`, got {y.get('type')!r}."
    )


def test_x_sort_descending_by_mean_mpg(vega_spec):
    encoding = vega_spec.get("encoding") or {}
    x = encoding.get("x") or {}
    sort = x.get("sort")
    assert sort is not None, (
        "Expected `encoding.x.sort` to be set so the x axis is sorted by mean MPG descending."
    )

    if isinstance(sort, str):
        assert sort == "-y", (
            f"Expected `encoding.x.sort` shorthand to be `'-y'` (descending by the y channel), got {sort!r}."
        )
        assert _y_aggregates_mean_mpg(encoding), (
            "When using `encoding.x.sort == '-y'`, the y channel must already aggregate "
            "`mean` of `Miles_per_Gallon`."
        )
        return

    assert isinstance(sort, dict), (
        f"Expected `encoding.x.sort` to be either the string `'-y'` or an object with "
        f"`op`, `field`, and `order`. Got: {sort!r}"
    )
    assert sort.get("op") == "mean", (
        f"Expected `encoding.x.sort.op == 'mean'`, got {sort.get('op')!r}."
    )
    assert sort.get("field") == "Miles_per_Gallon", (
        f"Expected `encoding.x.sort.field == 'Miles_per_Gallon'`, got {sort.get('field')!r}."
    )
    assert sort.get("order") == "descending", (
        f"Expected `encoding.x.sort.order == 'descending'`, got {sort.get('order')!r}."
    )


def test_tooltip_has_mean_and_count(vega_spec):
    encoding = vega_spec.get("encoding") or {}
    tooltip = encoding.get("tooltip")
    assert isinstance(tooltip, list), (
        "Expected `encoding.tooltip` to be a list/array of tooltip channel definitions."
    )
    assert len(tooltip) >= 2, (
        f"Expected `encoding.tooltip` to contain at least 2 entries, got {len(tooltip)}."
    )

    has_mean_mpg = False
    has_count = False
    for entry in tooltip:
        if not isinstance(entry, dict):
            continue
        aggregate = entry.get("aggregate")
        field = entry.get("field")
        if aggregate == "mean" and field == "Miles_per_Gallon":
            has_mean_mpg = True
        if aggregate == "count":
            has_count = True

    assert has_mean_mpg, (
        "Expected at least one tooltip entry to aggregate `mean` over `Miles_per_Gallon`."
    )
    assert has_count, (
        "Expected at least one tooltip entry to aggregate `count` "
        "(the count of cars per origin)."
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


def test_browser_renders_three_descending_bars(chart_preview_server):
    reason = (
        "The Altair-generated chart.html must render a single bar chart of average "
        "Miles_per_Gallon by Origin from the cars dataset. The chart must show one bar "
        "per origin (Europe, Japan, USA), with bars sorted in descending order of mean MPG."
    )
    truth = (
        f"Navigate to {chart_preview_server} in a browser. "
        "Wait for the Vega-Lite chart to finish rendering. "
        "Verify that the page has no JavaScript console errors. "
        "Verify that the rendered chart contains exactly 3 visible vertical bars. "
        "Verify that the x-axis tick labels are exactly the three strings: `Europe`, "
        "`Japan`, and `USA` (one label per bar, in some order). "
        "Verify that the heights of the bars are monotonically decreasing from the "
        "leftmost bar to the rightmost bar (i.e., the bars are sorted in descending "
        "order by their height, which represents mean Miles_per_Gallon). "
        "Hover the pointer over any bar and verify that a tooltip appears showing "
        "BOTH a mean Miles_per_Gallon value AND a car count for that origin."
    )
    verifier = PochiVerifier()
    result = verifier.verify(
        reason=reason,
        truth=truth,
        use_browser_agent=True,
        trajectory_dir="/logs/verifier/pochi/test_browser_renders_three_descending_bars",
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
