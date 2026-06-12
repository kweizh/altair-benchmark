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


def _mark_type(view: dict[str, Any]) -> str:
    mark = view.get("mark")
    if isinstance(mark, str):
        return mark
    if isinstance(mark, dict):
        return str(mark.get("type", ""))
    return ""


def _iter_all_params(spec: dict[str, Any]) -> list[dict[str, Any]]:
    """Collect every selection/param entry declared anywhere in the spec
    (top-level or inside any of the vconcat sub-views)."""
    params: list[dict[str, Any]] = []
    top = spec.get("params")
    if isinstance(top, list):
        params.extend([p for p in top if isinstance(p, dict)])
    for view in spec.get("vconcat", []) or []:
        if isinstance(view, dict) and isinstance(view.get("params"), list):
            params.extend([p for p in view["params"] if isinstance(p, dict)])
    return params


def _find_brush_param(spec: dict[str, Any]) -> dict[str, Any]:
    """Locate the interval selection limited to the x encoding."""
    for p in _iter_all_params(spec):
        sel = p.get("select")
        if isinstance(sel, dict) and sel.get("type") == "interval":
            encodings = sel.get("encodings") or []
            if list(encodings) == ["x"]:
                return p
    raise AssertionError(
        "Expected exactly one interval selection parameter whose "
        "`select.encodings == ['x']` (the focus/context brush), but none was found."
    )


def _scale_domain_ref_name(x_encoding: dict[str, Any]) -> str | None:
    scale = x_encoding.get("scale")
    if not isinstance(scale, dict):
        return None
    domain = scale.get("domain")
    if not isinstance(domain, dict):
        return None
    # Altair 5+ typically emits {"param": "..."}; older serializations used
    # {"selection": "..."}. Accept either.
    name = domain.get("param") or domain.get("selection")
    if isinstance(name, str):
        return name
    return None


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


def test_spec_is_vconcat_of_length_two(vega_spec):
    vconcat = vega_spec.get("vconcat")
    assert isinstance(vconcat, list), (
        "Top-level Vega-Lite spec must contain a `vconcat` array "
        "(focus chart stacked above context chart)."
    )
    assert len(vconcat) == 2, (
        f"Expected exactly 2 sub-views in the vconcat (focus + context), "
        f"found {len(vconcat)}."
    )


def test_interval_brush_selection_on_x(vega_spec):
    brush = _find_brush_param(vega_spec)
    sel = brush["select"]
    assert sel.get("type") == "interval", (
        f"Brush selection must be of `type` `interval`, got {sel.get('type')!r}."
    )
    assert list(sel.get("encodings") or []) == ["x"], (
        f"Brush selection must set `encodings == ['x']`, "
        f"got {sel.get('encodings')!r}."
    )
    assert isinstance(brush.get("name"), str) and brush["name"], (
        "Brush selection parameter must have a non-empty `name`."
    )


def test_upper_focus_view(vega_spec):
    vconcat = vega_spec["vconcat"]
    upper = vconcat[0]
    assert isinstance(upper, dict), "Upper (focus) view must be a Vega-Lite view object."

    assert _mark_type(upper) == "area", (
        f"Upper (focus) view must use `mark` type `area`, got {_mark_type(upper)!r}."
    )

    encoding = upper.get("encoding") or {}
    x = encoding.get("x") or {}
    assert x.get("field") == "date", (
        f"Upper view x encoding must map field `date`, got {x.get('field')!r}."
    )
    assert x.get("type") == "temporal", (
        f"Upper view x encoding must be of type `temporal`, got {x.get('type')!r}."
    )

    brush_name = _find_brush_param(vega_spec)["name"]
    domain_ref_name = _scale_domain_ref_name(x)
    assert domain_ref_name == brush_name, (
        "Upper view x encoding must bind its scale `domain` to the brush selection "
        f"(expected an object like {{'param': {brush_name!r}}} or "
        f"{{'selection': {brush_name!r}}}), but found scale={x.get('scale')!r}."
    )

    y = encoding.get("y") or {}
    assert y.get("field") == "price", (
        f"Upper view y encoding must map field `price`, got {y.get('field')!r}."
    )
    assert y.get("type") == "quantitative", (
        f"Upper view y encoding must be of type `quantitative`, got {y.get('type')!r}."
    )

    assert upper.get("width") == 600, (
        f"Upper (focus) view must have width=600, got {upper.get('width')!r}."
    )
    assert upper.get("height") == 250, (
        f"Upper (focus) view must have height=250, got {upper.get('height')!r}."
    )


def test_lower_context_view(vega_spec):
    vconcat = vega_spec["vconcat"]
    lower = vconcat[1]
    assert isinstance(lower, dict), "Lower (context) view must be a Vega-Lite view object."

    assert _mark_type(lower) == "area", (
        f"Lower (context) view must use `mark` type `area`, got {_mark_type(lower)!r}."
    )

    encoding = lower.get("encoding") or {}
    x = encoding.get("x") or {}
    assert x.get("field") == "date", (
        f"Lower view x encoding must map field `date`, got {x.get('field')!r}."
    )
    assert x.get("type") == "temporal", (
        f"Lower view x encoding must be of type `temporal`, got {x.get('type')!r}."
    )

    y = encoding.get("y") or {}
    assert y.get("field") == "price", (
        f"Lower view y encoding must map field `price`, got {y.get('field')!r}."
    )
    assert y.get("type") == "quantitative", (
        f"Lower view y encoding must be of type `quantitative`, got {y.get('type')!r}."
    )

    assert lower.get("width") == 600, (
        f"Lower (context) view must have width=600, got {lower.get('width')!r}."
    )
    assert lower.get("height") == 70, (
        f"Lower (context) view must have height=70, got {lower.get('height')!r}."
    )

    brush_name = _find_brush_param(vega_spec)["name"]
    lower_params = lower.get("params")
    assert isinstance(lower_params, list) and lower_params, (
        "Lower (context) view must declare a `params` array containing the brush selection "
        "(the brush is attached to this view via add_params)."
    )
    matching = []
    for p in lower_params:
        if not isinstance(p, dict):
            continue
        if p.get("name") != brush_name:
            continue
        sel = p.get("select")
        if isinstance(sel, dict) and sel.get("type") == "interval" \
                and list(sel.get("encodings") or []) == ["x"]:
            matching.append(p)
    assert matching, (
        f"Lower (context) view's `params` must include the interval brush "
        f"(name={brush_name!r}, select.type='interval', select.encodings=['x']). "
        f"Got params={lower_params!r}."
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


def test_browser_focus_context_brush(chart_preview_server):
    reason = (
        "The Altair-generated chart.html must render a classic Focus + Context "
        "(overview + detail) S&P 500 chart: two stacked area charts where the "
        "larger detail chart on top responds to an interval brush dragged on the "
        "slim context chart at the bottom by narrowing its x-axis domain to the "
        "selected time range."
    )
    truth = (
        f"Navigate to {chart_preview_server} in a browser. "
        "Wait for the Vega-Lite chart to finish rendering. "
        "Verify that the page contains two stacked area charts: a large detail "
        "chart on top (about 600x250 pixels) and a slim context/overview chart "
        "below it (about 600x70 pixels). Verify that the JavaScript console has "
        "no errors. Then, on the lower (slim) area chart, click and drag "
        "horizontally to select roughly the middle third of its horizontal "
        "extent, then release the mouse. Verify that after the drag, the upper "
        "(large) detail chart visibly rescales its x-axis: the time-axis tick "
        "labels and the visible area shape change so that the upper chart now "
        "shows only the dragged sub-range (its x-axis domain narrows to the "
        "brushed interval)."
    )
    verifier = PochiVerifier()
    result = verifier.verify(
        reason=reason,
        truth=truth,
        use_browser_agent=True,
        trajectory_dir="/logs/verifier/pochi/test_browser_focus_context_brush",
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
