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

PETAL_LENGTH_FIELDS = {"petalLength", "petal_length"}


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
    mt = _mark_type(vega_spec)
    assert mt == "bar", (
        f"Expected top-level `mark` to be `bar`, got `{mt}`. "
        "The chart should be built with `alt.Chart(...).mark_bar()`."
    )


def test_x_encoding_is_binned_petal_length_quantitative(vega_spec):
    encoding = vega_spec.get("encoding") or {}
    x = encoding.get("x")
    assert isinstance(x, dict), (
        "Expected `encoding.x` to be an object describing the binned petalLength field."
    )
    field = x.get("field")
    assert field in PETAL_LENGTH_FIELDS, (
        f"Expected `encoding.x.field` to be one of {sorted(PETAL_LENGTH_FIELDS)}, "
        f"got `{field}`."
    )
    type_ = x.get("type")
    assert type_ == "quantitative", (
        f"Expected `encoding.x.type` to be `quantitative`, got `{type_}`. "
        "URL-based sources require explicit type shorthands (e.g. `petalLength:Q`)."
    )
    bin_spec = x.get("bin")
    assert isinstance(bin_spec, dict), (
        f"Expected `encoding.x.bin` to be an object (e.g. `{{\"maxbins\": 20}}`), "
        f"got `{bin_spec!r}`. Use `alt.X('petalLength:Q').bin(maxbins=20)` or "
        "`alt.X('petalLength:Q', bin=alt.Bin(maxbins=20))`."
    )
    assert bin_spec.get("maxbins") == 20, (
        f"Expected `encoding.x.bin.maxbins` to be `20`, got `{bin_spec.get('maxbins')!r}`."
    )


def test_y_encoding_is_count_aggregate(vega_spec):
    encoding = vega_spec.get("encoding") or {}
    y = encoding.get("y")
    assert isinstance(y, dict), (
        "Expected `encoding.y` to be an object describing the count aggregate."
    )
    aggregate = y.get("aggregate")
    assert aggregate == "count", (
        f"Expected `encoding.y.aggregate` to be `count`, got `{aggregate!r}`. "
        "Use the `count()` shorthand on the y channel."
    )


def test_color_encoding_is_species_nominal(vega_spec):
    encoding = vega_spec.get("encoding") or {}
    color = encoding.get("color")
    assert isinstance(color, dict), (
        "Expected `encoding.color` to be an object referencing the species field."
    )
    field = color.get("field")
    assert field == "species", (
        f"Expected `encoding.color.field` to be `species`, got `{field!r}`."
    )
    type_ = color.get("type")
    assert type_ == "nominal", (
        f"Expected `encoding.color.type` to be `nominal`, got `{type_!r}`. "
        "URL-based sources require explicit type shorthands (e.g. `species:N`)."
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


def test_browser_renders_stacked_species_histogram(chart_preview_server):
    reason = (
        "The Altair-generated chart.html must render a binned histogram of iris "
        "`petalLength` (maxbins=20) with bars colored and stacked by `species`. "
        "All three iris species (setosa, versicolor, virginica) must appear in the "
        "legend and as distinct fill colors in the bars."
    )
    truth = (
        f"Navigate to {chart_preview_server} in a browser. "
        "Wait for the Vega-Lite chart to finish rendering. "
        "Verify the page has no JavaScript console errors. "
        "Verify the rendered chart contains visible bar (`rect`) marks along an x axis "
        "that represents binned petal length. "
        "Verify the bars are filled with three distinct colors and that the legend "
        "lists exactly three entries: `setosa`, `versicolor`, and `virginica`. "
        "Verify the bars are stacked (multiple species share the same x bin and are "
        "stacked vertically on top of each other, not placed side-by-side and not "
        "overlapping translucently)."
    )
    verifier = PochiVerifier()
    result = verifier.verify(
        reason=reason,
        truth=truth,
        use_browser_agent=True,
        trajectory_dir="/logs/verifier/pochi/test_browser_renders_stacked_species_histogram",
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
