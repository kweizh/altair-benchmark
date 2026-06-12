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
EXPECTED_TITLE = "IMDB Rating Distribution"


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
        if isinstance(text, list) and text and isinstance(text[0], str):
            return text[0]
    return ""


def _filter_to_text(filter_value: Any) -> str:
    """Render a Vega-Lite filter predicate as a comparable text blob."""
    if isinstance(filter_value, str):
        return filter_value
    try:
        return json.dumps(filter_value, sort_keys=True)
    except (TypeError, ValueError):
        return str(filter_value)


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
        f"Expected the top-level chart `mark` to be `bar`, got {mark!r}."
    )


def test_x_encoding_bins_imdb_rating_with_step(vega_spec):
    encoding = vega_spec.get("encoding") or {}
    x = encoding.get("x")
    assert isinstance(x, dict), (
        "Expected `encoding.x` to be an object referencing the IMDB_Rating field."
    )
    assert x.get("field") == "IMDB_Rating", (
        f"Expected `encoding.x.field` to be `\"IMDB_Rating\"`, got {x.get('field')!r}."
    )
    bin_def = x.get("bin")
    assert isinstance(bin_def, dict), (
        "Expected `encoding.x.bin` to be an object specifying `step`, "
        f"got {bin_def!r}."
    )
    step = bin_def.get("step")
    assert step == 0.5, (
        f"Expected `encoding.x.bin.step` to be `0.5`, got {step!r}."
    )


def test_y_encoding_is_count_aggregate(vega_spec):
    encoding = vega_spec.get("encoding") or {}
    y = encoding.get("y")
    assert isinstance(y, dict), (
        "Expected `encoding.y` to be an object with a `count` aggregate."
    )
    aggregate = y.get("aggregate")
    assert aggregate == "count", (
        f"Expected `encoding.y.aggregate` to equal `\"count\"`, got {aggregate!r}."
    )


def test_transform_filter_excludes_imdb_rating_nulls(vega_spec):
    transforms = vega_spec.get("transform")
    assert isinstance(transforms, list) and len(transforms) >= 1, (
        "Expected the spec to declare at least one top-level `transform` entry."
    )
    filter_entries = [
        t for t in transforms if isinstance(t, dict) and "filter" in t
    ]
    assert filter_entries, (
        "Expected at least one `transform` entry of type `filter`."
    )
    matched = False
    for entry in filter_entries:
        text = _filter_to_text(entry["filter"])
        references_field = "IMDB_Rating" in text
        excludes_null = (
            "null" in text.lower()
            or '"valid": true' in text
            or "'valid': true" in text
        )
        if references_field and excludes_null:
            matched = True
            break
    assert matched, (
        "Expected a `transform_filter` entry whose filter expression references "
        "`IMDB_Rating` and excludes null values "
        "(e.g. `datum.IMDB_Rating != null` or `{field: 'IMDB_Rating', valid: true}`). "
        f"Got: {filter_entries!r}"
    )


def test_title_is_imdb_rating_distribution(vega_spec):
    title = _title_text(vega_spec)
    assert title == EXPECTED_TITLE, (
        f"Expected the top-level chart title to be {EXPECTED_TITLE!r}, got {title!r}."
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


def test_browser_renders_histogram(chart_preview_server):
    reason = (
        "The Altair-generated chart.html must render a bar histogram of the movies "
        "dataset's IMDB_Rating field, binned with step=0.5, titled "
        f"'{EXPECTED_TITLE}', with null ratings filtered out inside the spec."
    )
    truth = (
        f"Navigate to {chart_preview_server} in a browser. "
        "Wait for the Vega-Lite chart to finish rendering. "
        "Verify that the page has no JavaScript console errors and that the "
        "rendered chart visibly contains multiple bar marks distributed across "
        "IMDB rating values along the x-axis (the x-axis labels should be numeric "
        "rating values in the approximate range 1-10), with the y-axis representing "
        f"counts. The chart title should display '{EXPECTED_TITLE}'."
    )
    verifier = PochiVerifier()
    result = verifier.verify(
        reason=reason,
        truth=truth,
        use_browser_agent=True,
        trajectory_dir="/logs/verifier/pochi/test_browser_renders_histogram",
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
