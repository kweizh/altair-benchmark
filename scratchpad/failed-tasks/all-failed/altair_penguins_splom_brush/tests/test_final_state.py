import json
import os
import re
import socket
import subprocess
import sys
from typing import Any

import pytest
from pochi_verifier import PochiVerifier
from xprocess import ProcessStarter

PROJECT_DIR = "/home/user/myproject"
SOLUTION_FILE = os.path.join(PROJECT_DIR, "solution.py")
CHART_HTML = os.path.join(PROJECT_DIR, "chart.html")
HTTP_PORT = 8765


# ---------------------------------------------------------------------------
# Helpers to extract the Vega-Lite spec from the generated chart.html
# ---------------------------------------------------------------------------


def _read_chart_html() -> str:
    assert os.path.isfile(CHART_HTML), (
        f"Expected the executor to generate {CHART_HTML} but the file was not found."
    )
    with open(CHART_HTML, "r", encoding="utf-8") as fh:
        return fh.read()


def _extract_vega_spec(html: str) -> dict[str, Any]:
    # Strategy 1: an inline <script type="application/json"> block holding the spec.
    inline_match = re.search(
        r"<script[^>]*type=[\"']application/json[\"'][^>]*>(.*?)</script>",
        html,
        flags=re.DOTALL | re.IGNORECASE,
    )
    if inline_match:
        try:
            return json.loads(inline_match.group(1).strip())
        except json.JSONDecodeError:
            pass

    # Strategy 2: a vegaEmbed("...", { ... }) call where the second argument is the spec.
    embed_match = re.search(
        r"vegaEmbed\([^,]+,\s*(\{.*?\})\s*[,)]",
        html,
        flags=re.DOTALL,
    )
    if embed_match:
        try:
            return json.loads(embed_match.group(1))
        except json.JSONDecodeError:
            pass

    # Strategy 3: a `var spec = { ... };` assignment.
    var_match = re.search(
        r"(?:var|const|let)\s+spec\s*=\s*(\{.*?\})\s*;",
        html,
        flags=re.DOTALL,
    )
    if var_match:
        try:
            return json.loads(var_match.group(1))
        except json.JSONDecodeError:
            pass

    raise AssertionError(
        "Could not locate or parse the Vega-Lite spec embedded in chart.html. "
        "Expected either an inline <script type='application/json'> block or a "
        "vegaEmbed(..., {...}) call carrying the spec."
    )


@pytest.fixture(scope="session")
def vega_spec() -> dict[str, Any]:
    # Solver execution: re-run solution.py so the test is deterministic.
    if os.path.exists(CHART_HTML):
        os.remove(CHART_HTML)
    result = subprocess.run(
        [sys.executable, SOLUTION_FILE],
        capture_output=True,
        text=True,
        cwd=PROJECT_DIR,
    )
    assert result.returncode == 0, (
        f"Running the executor's solution.py failed with exit code {result.returncode}.\n"
        f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
    )
    html = _read_chart_html()
    return _extract_vega_spec(html)


# ---------------------------------------------------------------------------
# Spec-level structural assertions
# ---------------------------------------------------------------------------


def test_chart_html_exists_and_nonempty(vega_spec: dict[str, Any]):
    assert os.path.isfile(CHART_HTML), f"chart.html not found at {CHART_HTML}"
    assert os.path.getsize(CHART_HTML) > 0, "chart.html exists but is empty."


def test_repeat_block_has_row_and_column(vega_spec: dict[str, Any]):
    repeat = vega_spec.get("repeat")
    assert isinstance(repeat, dict), (
        "Expected the top-level Vega-Lite spec to contain a 'repeat' object with 'row' and 'column' arrays."
    )
    row = repeat.get("row")
    column = repeat.get("column")
    assert isinstance(row, list) and len(row) >= 3, (
        f"Expected 'repeat.row' to be a list with at least 3 field names, got: {row!r}"
    )
    assert isinstance(column, list) and len(column) >= 3, (
        f"Expected 'repeat.column' to be a list with at least 3 field names, got: {column!r}"
    )


def _inner_spec(vega_spec: dict[str, Any]) -> dict[str, Any]:
    spec = vega_spec.get("spec")
    assert isinstance(spec, dict), (
        "Expected the top-level Vega-Lite spec to embed a child 'spec' object for the repeated cell."
    )
    return spec


def test_mark_is_point(vega_spec: dict[str, Any]):
    spec = _inner_spec(vega_spec)
    mark = spec.get("mark")
    if isinstance(mark, str):
        assert mark == "point", f"Expected mark 'point', got {mark!r}."
    elif isinstance(mark, dict):
        assert mark.get("type") == "point", (
            f"Expected mark.type 'point', got {mark.get('type')!r}."
        )
    else:
        raise AssertionError(
            f"Expected the repeated cell to use a 'point' mark, got mark={mark!r}."
        )


def _find_interval_param(spec: dict[str, Any]) -> dict[str, Any]:
    params = spec.get("params")
    assert isinstance(params, list) and params, (
        "Expected the repeated cell spec to declare at least one selection parameter via 'params'."
    )
    for param in params:
        if not isinstance(param, dict):
            continue
        select = param.get("select")
        if isinstance(select, dict) and select.get("type") == "interval":
            return param
        if isinstance(select, str) and select == "interval":
            return param
    raise AssertionError(
        "Expected an interval selection parameter (select.type == 'interval') in the repeated cell spec, "
        f"got params={params!r}."
    )


def test_interval_selection_over_x_and_y(vega_spec: dict[str, Any]):
    spec = _inner_spec(vega_spec)
    param = _find_interval_param(spec)
    select = param.get("select")
    assert isinstance(select, dict), (
        "Expected the interval selection to declare 'encodings' via a select object."
    )
    encodings = select.get("encodings")
    assert isinstance(encodings, list), (
        f"Expected 'select.encodings' to be a list, got {encodings!r}."
    )
    assert "x" in encodings and "y" in encodings, (
        f"Expected the interval selection to project over both 'x' and 'y' encodings, got {encodings!r}."
    )


def test_color_encoding_uses_brush_condition(vega_spec: dict[str, Any]):
    spec = _inner_spec(vega_spec)
    encoding = spec.get("encoding")
    assert isinstance(encoding, dict), "Expected an 'encoding' block in the repeated cell spec."
    color = encoding.get("color")
    assert isinstance(color, dict), (
        f"Expected encoding.color to be an object using a conditional encoding, got {color!r}."
    )
    condition = color.get("condition")
    assert condition is not None, (
        "Expected encoding.color to include a 'condition' clause referencing the brush parameter."
    )
    # condition can be a single dict or a list of dicts; we just need one that references a param.
    candidates = condition if isinstance(condition, list) else [condition]
    interval_param_name = _find_interval_param(spec).get("name")
    referenced_params = []
    for entry in candidates:
        if isinstance(entry, dict) and "param" in entry:
            referenced_params.append(entry["param"])
    assert referenced_params, (
        f"Expected encoding.color.condition to reference a selection parameter via 'param', got {condition!r}."
    )
    assert interval_param_name in referenced_params, (
        "Expected encoding.color.condition to reference the interval selection parameter "
        f"(name={interval_param_name!r}), but referenced parameters were {referenced_params!r}."
    )
    # The unselected branch should resolve to a value (commonly 'lightgray').
    value = color.get("value")
    if isinstance(value, str):
        assert value.lower() == "lightgray", (
            f"Expected unselected color value to be 'lightgray', got {value!r}."
        )


def test_xy_scales_zero_false(vega_spec: dict[str, Any]):
    spec = _inner_spec(vega_spec)
    encoding = spec.get("encoding", {})
    x_enc = encoding.get("x", {})
    y_enc = encoding.get("y", {})
    x_scale = x_enc.get("scale") if isinstance(x_enc, dict) else None
    y_scale = y_enc.get("scale") if isinstance(y_enc, dict) else None
    assert isinstance(x_scale, dict), (
        f"Expected encoding.x to declare a 'scale' object with zero=false, got {x_enc!r}."
    )
    assert isinstance(y_scale, dict), (
        f"Expected encoding.y to declare a 'scale' object with zero=false, got {y_enc!r}."
    )
    assert x_scale.get("zero") is False, (
        f"Expected encoding.x.scale.zero to be false, got {x_scale.get('zero')!r}."
    )
    assert y_scale.get("zero") is False, (
        f"Expected encoding.y.scale.zero to be false, got {y_scale.get('zero')!r}."
    )


# ---------------------------------------------------------------------------
# Browser-based verification of the rendered HTML
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def http_server(xprocess, vega_spec):
    # vega_spec dependency ensures chart.html has been (re)generated.
    class Starter(ProcessStarter):
        name = "altair_chart_http"
        args = [sys.executable, "-m", "http.server", str(HTTP_PORT)]
        env = os.environ.copy()
        popen_kwargs = {
            "cwd": PROJECT_DIR,
            "text": True,
        }
        timeout = 30
        terminate_on_interrupt = True

        def startup_check(self):
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                return s.connect_ex(("localhost", HTTP_PORT)) == 0

    xprocess.ensure(Starter.name, Starter)
    yield f"http://localhost:{HTTP_PORT}/chart.html"
    info = xprocess.getinfo(Starter.name)
    info.terminate()


def test_browser_renders_grid_and_brush(http_server: str):
    verifier = PochiVerifier()
    reason = (
        "The generated chart is a Scatter PLOt Matrix on the Penguins dataset built with "
        "alt.repeat over four quantitative features, with a single linked interval brush. "
        "When rendered in a browser, the page must show a grid of scatter cells and a working "
        "interval-selection brush that links highlighting across the cells."
    )
    truth = (
        f"Navigate to {http_server} and wait for the Vega-Altair chart to finish rendering. "
        "Verify that the page contains a grid of at least 9 distinct scatter sub-plots arranged "
        "as a repeated matrix (rows x columns produced by the Altair repeat operator). "
        "Drag a rectangle inside any one of the cells using the mouse. After dragging, verify that "
        "an interval-selection brush rectangle is visible in that cell, AND that points falling "
        "outside the brushed rectangle in every other cell turn light gray while points inside the "
        "brush remain colored by Species. Release the mouse and confirm the brush rectangle persists. "
        "If any of these conditions fail, the verification must fail."
    )
    result = verifier.verify(
        reason=reason,
        truth=truth,
        use_browser_agent=True,
        trajectory_dir="/logs/verifier/pochi/test_browser_renders_grid_and_brush",
    )
    assert result.status == "pass", f"Browser verification failed: {result.reason}"
