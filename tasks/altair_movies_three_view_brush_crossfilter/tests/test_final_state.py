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


def _collect_params(node: Any) -> list[dict[str, Any]]:
    """Recursively collect every `params` entry in a spec tree."""
    found: list[dict[str, Any]] = []
    if isinstance(node, dict):
        params = node.get("params")
        if isinstance(params, list):
            for p in params:
                if isinstance(p, dict):
                    found.append(p)
        for v in node.values():
            found.extend(_collect_params(v))
    elif isinstance(node, list):
        for item in node:
            found.extend(_collect_params(item))
    return found


def _find_interval_param_name(spec: dict[str, Any]) -> str:
    for p in _collect_params(spec):
        sel = p.get("select")
        if isinstance(sel, dict) and sel.get("type") == "interval":
            name = p.get("name")
            if isinstance(name, str) and name:
                return name
        elif isinstance(sel, str) and sel == "interval":
            name = p.get("name")
            if isinstance(name, str) and name:
                return name
    return ""


def _filter_references_param(filter_obj: Any, param_name: str) -> bool:
    """Return True if a `transform.filter` entry references the given selection/param."""
    if isinstance(filter_obj, dict):
        if filter_obj.get("param") == param_name:
            return True
        if filter_obj.get("selection") == param_name:
            return True
    if isinstance(filter_obj, str):
        # Some older specs reference selections by name inside expression strings.
        return param_name in filter_obj
    return False


def _transforms_for(view: dict[str, Any]) -> list[dict[str, Any]]:
    t = view.get("transform")
    return t if isinstance(t, list) else []


def _filter_expressions(view: dict[str, Any]) -> list[str]:
    """Collect every transform filter expression (as a string) defined on a view."""
    exprs: list[str] = []
    for t in _transforms_for(view):
        if not isinstance(t, dict):
            continue
        if "filter" not in t:
            continue
        f = t["filter"]
        if isinstance(f, str):
            exprs.append(f)
        elif isinstance(f, dict):
            # FieldEqualPredicate / FieldRangePredicate / etc.
            try:
                exprs.append(json.dumps(f))
            except (TypeError, ValueError):  # pragma: no cover
                exprs.append(str(f))
    return exprs


def _has_null_filter(view: dict[str, Any], field: str) -> bool:
    for expr in _filter_expressions(view):
        if field not in expr:
            continue
        lowered = expr.lower()
        # Catch any of: `datum.field != null`, `datum.field !== null`, `valid(datum.field)`,
        # `isValid`, FieldValidPredicate JSON, etc.
        if "null" in lowered or "valid" in lowered:
            return True
    return False


def _references_param_in_transforms(view: dict[str, Any], param_name: str) -> bool:
    for t in _transforms_for(view):
        if not isinstance(t, dict):
            continue
        if "filter" in t and _filter_references_param(t["filter"], param_name):
            return True
    return False


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
def views(vega_spec) -> dict[str, dict[str, Any]]:
    vconcat = vega_spec.get("vconcat")
    assert isinstance(vconcat, list) and len(vconcat) == 2, (
        f"Top-level spec must contain a `vconcat` array of length 2, "
        f"got: {type(vconcat).__name__} (len={len(vconcat) if isinstance(vconcat, list) else 'n/a'})."
    )
    scatter = vconcat[0]
    bottom = vconcat[1]
    assert isinstance(scatter, dict), "vconcat[0] (scatter view) must be a dict."
    assert isinstance(bottom, dict), "vconcat[1] (bottom row) must be a dict."

    hconcat = bottom.get("hconcat")
    assert isinstance(hconcat, list) and len(hconcat) == 2, (
        f"vconcat[1] must contain an `hconcat` array of length 2 (bar | histogram), "
        f"got: {type(hconcat).__name__} (len={len(hconcat) if isinstance(hconcat, list) else 'n/a'})."
    )
    bar = hconcat[0]
    hist = hconcat[1]
    assert isinstance(bar, dict), "hconcat[0] (bar view) must be a dict."
    assert isinstance(hist, dict), "hconcat[1] (histogram view) must be a dict."
    return {"scatter": scatter, "bar": bar, "hist": hist}


@pytest.fixture(scope="session")
def brush_name(vega_spec) -> str:
    name = _find_interval_param_name(vega_spec)
    assert name, (
        "Expected at least one selection parameter with `select.type == 'interval'` "
        "(the crossfilter brush). None was found anywhere in the spec."
    )
    return name


def test_chart_html_exists():
    assert os.path.isfile(BUILD_SCRIPT), (
        f"Expected build script {BUILD_SCRIPT} to exist."
    )
    assert os.path.isfile(CHART_HTML), (
        f"Expected {CHART_HTML} to be produced by `python3 build_chart.py`."
    )
    assert os.path.getsize(CHART_HTML) > 0, f"{CHART_HTML} is empty."


def test_three_view_layout(views):
    # The fixture already enforces vconcat=2 and hconcat=2; this test documents it.
    assert "mark" in views["scatter"] or "encoding" in views["scatter"], (
        "Scatter view (vconcat[0]) should describe a mark/encoding."
    )
    assert "mark" in views["bar"] or "encoding" in views["bar"], (
        "Bar view (hconcat[0]) should describe a mark/encoding."
    )
    assert "mark" in views["hist"] or "encoding" in views["hist"], (
        "Histogram view (hconcat[1]) should describe a mark/encoding."
    )


def test_interval_brush_param_declared(brush_name):
    assert brush_name, f"Expected interval brush param name, got {brush_name!r}."


def test_scatter_view(views, brush_name):
    scatter = views["scatter"]
    assert _mark_type(scatter) == "point", (
        f"Scatter view mark must be `point`, got {_mark_type(scatter)!r}."
    )
    encoding = scatter.get("encoding") or {}

    x = encoding.get("x") or {}
    assert x.get("field") == "IMDB_Rating", (
        f"Scatter x field must be 'IMDB_Rating', got {x.get('field')!r}."
    )
    y = encoding.get("y") or {}
    assert y.get("field") == "Rotten_Tomatoes_Rating", (
        f"Scatter y field must be 'Rotten_Tomatoes_Rating', got {y.get('field')!r}."
    )

    color = encoding.get("color")
    assert isinstance(color, dict), (
        f"Scatter encoding.color must be a dict with a condition, got {type(color).__name__}."
    )
    condition = color.get("condition")
    assert isinstance(condition, dict), (
        f"Scatter encoding.color must include a `condition` object, got {condition!r}."
    )
    ref_name = condition.get("param") or condition.get("selection")
    assert ref_name == brush_name, (
        f"Scatter color condition must reference the brush param "
        f"({brush_name!r}), got {ref_name!r}."
    )
    fallback = color.get("value")
    assert fallback == "lightgray", (
        f"Scatter color non-condition fallback (`value`) must be 'lightgray', got {fallback!r}."
    )


def _count_axis_and_field_axis(encoding: dict[str, Any]) -> tuple[str, str]:
    """Return (count_axis, field_axis) where one encoding aggregates count
    and the other has a `field`. Both will be one of 'x' or 'y'."""
    x = encoding.get("x") or {}
    y = encoding.get("y") or {}
    if isinstance(x, dict) and x.get("aggregate") == "count":
        return "x", "y"
    if isinstance(y, dict) and y.get("aggregate") == "count":
        return "y", "x"
    return "", ""


def test_bar_view(views, brush_name):
    bar = views["bar"]
    assert _mark_type(bar) == "bar", (
        f"Bar view mark must be `bar`, got {_mark_type(bar)!r}."
    )
    encoding = bar.get("encoding") or {}
    count_axis, field_axis = _count_axis_and_field_axis(encoding)
    assert count_axis and field_axis, (
        "Bar view must have exactly one positional encoding with aggregate 'count'. "
        f"Got encoding x={encoding.get('x')!r}, y={encoding.get('y')!r}."
    )
    other = encoding.get(field_axis) or {}
    assert isinstance(other, dict) and other.get("field") == "Major_Genre", (
        f"Bar view's non-count positional axis ({field_axis}) must have "
        f"field 'Major_Genre', got {other.get('field')!r}."
    )

    assert _references_param_in_transforms(bar, brush_name), (
        f"Bar view's transforms must include a `filter` referencing the brush param "
        f"({brush_name!r}). Got transforms: {bar.get('transform')!r}."
    )


def test_histogram_view(views, brush_name):
    hist = views["hist"]
    assert _mark_type(hist) == "bar", (
        f"Histogram view mark must be `bar`, got {_mark_type(hist)!r}."
    )
    encoding = hist.get("encoding") or {}
    count_axis, field_axis = _count_axis_and_field_axis(encoding)
    assert count_axis and field_axis, (
        "Histogram view must have one positional encoding with aggregate 'count'. "
        f"Got encoding x={encoding.get('x')!r}, y={encoding.get('y')!r}."
    )
    bin_enc = encoding.get(field_axis) or {}
    assert isinstance(bin_enc, dict) and bin_enc.get("field") == "IMDB_Rating", (
        f"Histogram view's binned axis ({field_axis}) must have field 'IMDB_Rating', "
        f"got {bin_enc.get('field')!r}."
    )
    bin_value = bin_enc.get("bin")
    if isinstance(bin_value, dict):
        assert bin_value.get("maxbins") == 20, (
            f"Histogram bin maxbins must be 20, got {bin_value!r}."
        )
    else:
        raise AssertionError(
            f"Histogram view's binned axis must declare `bin: {{maxbins: 20}}`, "
            f"got bin={bin_value!r}."
        )

    assert _references_param_in_transforms(hist, brush_name), (
        f"Histogram view's transforms must include a `filter` referencing the brush param "
        f"({brush_name!r}). Got transforms: {hist.get('transform')!r}."
    )


def test_null_filters_present(views):
    scatter = views["scatter"]
    bar = views["bar"]
    hist = views["hist"]

    assert _has_null_filter(scatter, "IMDB_Rating"), (
        "Scatter view must include a transform `filter` excluding null IMDB_Rating rows. "
        f"Got filters: {_filter_expressions(scatter)!r}."
    )
    assert _has_null_filter(scatter, "Rotten_Tomatoes_Rating"), (
        "Scatter view must include a transform `filter` excluding null "
        "Rotten_Tomatoes_Rating rows. "
        f"Got filters: {_filter_expressions(scatter)!r}."
    )
    assert _has_null_filter(bar, "IMDB_Rating"), (
        "Bar view must include a transform `filter` excluding null IMDB_Rating rows. "
        f"Got filters: {_filter_expressions(bar)!r}."
    )
    assert _has_null_filter(hist, "IMDB_Rating"), (
        "Histogram view must include a transform `filter` excluding null IMDB_Rating rows. "
        f"Got filters: {_filter_expressions(hist)!r}."
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


def test_browser_crossfilter_brush(chart_preview_server):
    reason = (
        "The Altair-generated chart.html must render a three-view crossfilter dashboard for the "
        "movies dataset: (1) a scatter plot of IMDB_Rating vs Rotten_Tomatoes_Rating with a 2D "
        "brush, (2) a bar chart of count() by Major_Genre, and (3) a histogram of IMDB_Rating. "
        "Dragging the brush on the scatter plot must crossfilter the bar chart and histogram."
    )
    truth = (
        f"Navigate to {chart_preview_server} in a headless browser and wait for the Vega-Lite "
        "chart to finish rendering. "
        "Verify the page has no JavaScript console errors and that three chart panels are visible: "
        "a scatter plot of points on top, and a bar chart (counts by Major_Genre) and a histogram "
        "(binned IMDB_Rating counts) side-by-side underneath. "
        "Record the heights of the bars in the bar chart by reading the rendered SVG <rect> "
        "elements (e.g., via document.querySelectorAll on the bar chart group). "
        "Then perform a mouse drag inside the scatter plot to draw an interval brush over a "
        "sub-region of the scatter (e.g., drag from roughly (chartX1, chartY1) to (chartX2, chartY2) "
        "covering only part of the data, not the whole plot). Wait for the dashboard to re-render. "
        "Verify that the bar heights captured AFTER the drag differ from the bars captured BEFORE "
        "the drag (the crossfilter has shrunk the bar chart). Also verify the histogram bars have "
        "changed (the binned counts also crossfilter). "
        "Verification passes only if (a) three panels are visible, (b) no JS errors are logged, "
        "and (c) the bar chart bar heights/counts change after the brush drag."
    )
    verifier = PochiVerifier()
    result = verifier.verify(
        reason=reason,
        truth=truth,
        use_browser_agent=True,
        trajectory_dir="/logs/verifier/pochi/test_browser_crossfilter_brush",
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
