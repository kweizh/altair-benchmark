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

EXPECTED_TITLE = "MPG vs Horsepower (threshold)"
EXPECTED_SLIDER_NAME = "HP threshold: "


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


def _mark_type(spec_or_layer: dict[str, Any]) -> str:
    mark = spec_or_layer.get("mark")
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


def test_mark_is_point(vega_spec):
    assert _mark_type(vega_spec) == "point", (
        f"Expected a single chart with mark type `point`, got mark "
        f"`{vega_spec.get('mark')!r}`."
    )


def test_slider_bound_parameter(vega_spec) -> None:
    params = vega_spec.get("params") or []
    assert isinstance(params, list) and len(params) >= 1, (
        "Expected the spec to declare at least one top-level parameter."
    )
    range_params = []
    for p in params:
        if not isinstance(p, dict):
            continue
        bind = p.get("bind")
        if isinstance(bind, dict) and bind.get("input") == "range":
            range_params.append(p)
    assert len(range_params) == 1, (
        f"Expected exactly one parameter bound to a `range` input, found "
        f"{len(range_params)}."
    )
    param = range_params[0]
    bind = param["bind"]
    assert bind.get("min") == 50, (
        f"Expected slider binding `min == 50`, got {bind.get('min')!r}."
    )
    assert bind.get("max") == 250, (
        f"Expected slider binding `max == 250`, got {bind.get('max')!r}."
    )
    assert bind.get("step") == 10, (
        f"Expected slider binding `step == 10`, got {bind.get('step')!r}."
    )
    assert bind.get("name") == EXPECTED_SLIDER_NAME, (
        f"Expected slider binding `name == {EXPECTED_SLIDER_NAME!r}`, "
        f"got {bind.get('name')!r}."
    )
    assert param.get("value") == 150, (
        f"Expected parameter initial `value == 150`, got {param.get('value')!r}."
    )
    assert isinstance(param.get("name"), str) and len(param["name"]) > 0, (
        "Expected the slider-bound parameter to have a non-empty `name` field."
    )


def _get_slider_param_name(spec: dict[str, Any]) -> str:
    for p in spec.get("params") or []:
        if not isinstance(p, dict):
            continue
        bind = p.get("bind")
        if isinstance(bind, dict) and bind.get("input") == "range":
            name = p.get("name")
            assert isinstance(name, str) and name, (
                "Slider-bound parameter must have a non-empty `name` field."
            )
            return name
    raise AssertionError("No slider-bound parameter found in spec.")


def test_x_and_y_encodings(vega_spec) -> None:
    encoding = vega_spec.get("encoding") or {}
    x = encoding.get("x") or {}
    y = encoding.get("y") or {}
    assert x.get("field") == "Horsepower", (
        f"Expected `encoding.x.field == 'Horsepower'`, got {x.get('field')!r}."
    )
    assert y.get("field") == "Miles_per_Gallon", (
        f"Expected `encoding.y.field == 'Miles_per_Gallon'`, got {y.get('field')!r}."
    )


def test_conditional_color_encoding(vega_spec) -> None:
    encoding = vega_spec.get("encoding") or {}
    color = encoding.get("color")
    assert isinstance(color, dict), (
        f"Expected `encoding.color` to be a conditional value encoding object, "
        f"got {type(color).__name__}."
    )
    condition = color.get("condition")
    # Vega-Lite allows either a single dict or a list of conditions.
    if isinstance(condition, list):
        assert len(condition) >= 1, (
            "Expected at least one entry in `encoding.color.condition`."
        )
        first_cond = condition[0]
    else:
        first_cond = condition
    assert isinstance(first_cond, dict), (
        f"Expected the color condition to be an object, got {type(first_cond).__name__}."
    )
    test_expr = str(first_cond.get("test", ""))
    assert test_expr, (
        "Expected the color condition to define a `test` expression."
    )

    param_name = _get_slider_param_name(vega_spec)
    assert param_name in test_expr, (
        f"Expected the color condition's `test` expression to reference the "
        f"parameter name `{param_name}`, got: {test_expr!r}."
    )
    # Look for `datum.Horsepower` reference (allow any whitespace).
    assert re.search(r"datum\s*\.\s*Horsepower", test_expr), (
        f"Expected the color condition's `test` expression to reference "
        f"`datum.Horsepower`, got: {test_expr!r}."
    )
    assert "<" in test_expr, (
        f"Expected the color condition's `test` expression to use the `<` "
        f"comparison, got: {test_expr!r}."
    )

    assert first_cond.get("value") == "steelblue", (
        f"Expected the color condition's `value` to be 'steelblue', "
        f"got {first_cond.get('value')!r}."
    )
    assert color.get("value") == "orange", (
        f"Expected the otherwise color `value` to be 'orange', "
        f"got {color.get('value')!r}."
    )


def test_chart_title(vega_spec) -> None:
    title = vega_spec.get("title")
    if isinstance(title, dict):
        title_text = title.get("text")
    else:
        title_text = title
    assert title_text == EXPECTED_TITLE, (
        f"Expected chart title to be exactly {EXPECTED_TITLE!r}, got {title_text!r}."
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


def test_browser_slider_drives_color_threshold(chart_preview_server):
    reason = (
        "The Altair-generated chart.html must render an interactive scatter plot of "
        "Horsepower vs. Miles_per_Gallon from the cars dataset, controlled by a horizontal "
        "range slider labelled 'HP threshold: '. With the slider at its initial value 150, "
        "points whose Horsepower is below the threshold must be colored steelblue and points "
        "at or above the threshold must be colored orange. Moving the slider to 200 must "
        "visibly shift the color split so that more points are colored steelblue."
    )
    truth = (
        f"Navigate to {chart_preview_server} in a browser. "
        "Wait for the Vega-Lite chart to finish rendering. "
        "Verify that the page has no JavaScript console errors. "
        "Verify a slider input labelled 'HP threshold: ' is visible (either above or below "
        "the chart) and its current numeric value is 150. "
        "Verify the rendered scatter plot's x-axis is labelled with Horsepower and y-axis with "
        "Miles per Gallon (or Miles_per_Gallon). "
        "Verify that, at threshold 150, points clearly split into two color groups: roughly all "
        "points with Horsepower < 150 are colored steelblue (blue) and all points with "
        "Horsepower >= 150 are colored orange. "
        "Then programmatically change the slider value to 200 (for example, find the slider "
        "input element via the DOM, set its value to 200, and dispatch an 'input' and 'change' "
        "event so the chart updates), wait for the chart to re-render, and verify that the "
        "boundary between steelblue and orange points has visibly shifted to the right: "
        "strictly more points are now steelblue than were steelblue at threshold 150."
    )
    verifier = PochiVerifier()
    result = verifier.verify(
        reason=reason,
        truth=truth,
        use_browser_agent=True,
        trajectory_dir="/logs/verifier/pochi/test_browser_slider_drives_color_threshold",
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
