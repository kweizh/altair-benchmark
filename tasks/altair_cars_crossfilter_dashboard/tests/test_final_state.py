import json
import os
import re
import socket
import subprocess
import sys

import pytest
from xprocess import ProcessStarter

try:  # pochi-verifier is installed in the verifier image
    from pochi_verifier import PochiVerifier
except Exception:  # pragma: no cover - environment-specific
    PochiVerifier = None  # type: ignore[assignment]


PROJECT_DIR = "/home/user/myproject"
SOLUTION_PATH = os.path.join(PROJECT_DIR, "solution.py")
CHART_HTML = os.path.join(PROJECT_DIR, "chart.html")
HTTP_PORT = 8765
BASE_URL = f"http://localhost:{HTTP_PORT}"


# ----------------------------- helpers ---------------------------------------


def _normalize_mark(mark):
    """Return the mark type string regardless of shorthand or object form."""
    if isinstance(mark, str):
        return mark
    if isinstance(mark, dict):
        return mark.get("type")
    return None


def _extract_spec_from_html(html_text: str) -> dict:
    """Pull the Vega-Lite JSON spec embedded in an Altair-generated chart.html."""
    # Altair writes either `var spec = {...};` or `vegaEmbed("#vis", {...}, ...)`
    patterns = [
        r"var\s+spec\s*=\s*(\{.*?\});",
        r"vegaEmbed\([^,]+,\s*(\{.*?\})\s*,",
    ]
    for pat in patterns:
        m = re.search(pat, html_text, re.DOTALL)
        if m:
            return json.loads(m.group(1))
    raise AssertionError(
        "Could not locate an embedded Vega-Lite spec in chart.html "
        "(expected a `var spec = {...};` or `vegaEmbed(\"#vis\", {...}, ...)` block)."
    )


def _find_brush_param(view: dict):
    """Return the first interval-selection param whose encodings cover x AND y."""
    params = view.get("params") or []
    for p in params:
        sel = p.get("select")
        if isinstance(sel, dict) and sel.get("type") == "interval":
            encs = sel.get("encodings") or []
            if "x" in encs and "y" in encs:
                return p
    return None


def _transform_filters_for_param(view: dict, param_name: str):
    """Yield every transform entry that filters on the given selection param name."""
    out = []
    for t in view.get("transform") or []:
        f = t.get("filter")
        if isinstance(f, dict) and f.get("param") == param_name:
            out.append(t)
        elif isinstance(f, str) and param_name in f:
            out.append(t)
    return out


# ----------------------------- fixtures --------------------------------------


@pytest.fixture(scope="session")
def run_solution():
    """Execute the solver's solution.py and ensure chart.html is produced."""
    assert os.path.isfile(SOLUTION_PATH), (
        f"solution.py is missing at {SOLUTION_PATH}; the executor did not produce it."
    )
    if os.path.exists(CHART_HTML):
        os.remove(CHART_HTML)
    proc = subprocess.run(
        [sys.executable, "solution.py"],
        cwd=PROJECT_DIR,
        capture_output=True,
        text=True,
        timeout=300,
    )
    assert proc.returncode == 0, (
        f"`python solution.py` exited with code {proc.returncode}.\n"
        f"stdout:\n{proc.stdout}\nstderr:\n{proc.stderr}"
    )
    assert os.path.isfile(CHART_HTML), (
        f"Expected chart.html artifact at {CHART_HTML} after running solution.py, "
        f"but it was not created."
    )
    yield CHART_HTML


@pytest.fixture(scope="session")
def chart_spec(run_solution):
    """Parse and cache the Vega-Lite JSON spec embedded in chart.html."""
    with open(run_solution, "r", encoding="utf-8") as f:
        html_text = f.read()
    spec = _extract_spec_from_html(html_text)
    assert isinstance(spec, dict), "Parsed Vega-Lite spec must be a JSON object."
    return spec


@pytest.fixture(scope="session")
def static_server(run_solution, xprocess):
    """Serve the project directory so the browser verifier can load chart.html."""

    class Starter(ProcessStarter):
        name = "altair_static_server"
        args = [sys.executable, "-m", "http.server", str(HTTP_PORT)]
        env = os.environ.copy()
        popen_kwargs = {"cwd": PROJECT_DIR, "text": True}
        timeout = 60
        terminate_on_interrupt = True

        def startup_check(self):
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                return s.connect_ex(("localhost", HTTP_PORT)) == 0

    xprocess.ensure(Starter.name, Starter)
    yield BASE_URL
    info = xprocess.getinfo(Starter.name)
    info.terminate()


@pytest.fixture(scope="session")
def views(chart_spec):
    """Decompose the top-level (A | B) & C layout into its three sub-views."""
    vconcat = chart_spec.get("vconcat")
    assert isinstance(vconcat, list) and len(vconcat) == 2, (
        f"Top-level spec must be a vconcat of length 2, got: {type(vconcat).__name__} "
        f"with {len(vconcat) if isinstance(vconcat, list) else 'n/a'} entries."
    )
    top_row = vconcat[0]
    hconcat = top_row.get("hconcat")
    assert isinstance(hconcat, list) and len(hconcat) == 2, (
        f"First vconcat entry must contain an hconcat of length 2, got: "
        f"{type(hconcat).__name__} with "
        f"{len(hconcat) if isinstance(hconcat, list) else 'n/a'} entries."
    )
    return {"A": hconcat[0], "B": hconcat[1], "C": vconcat[1]}


# ----------------------------- spec checks -----------------------------------


def test_layout_is_A_pipe_B_amp_C(views):
    """Layout must be (A | B) & C — i.e. vconcat[hconcat[A, B], C]."""
    assert "A" in views and "B" in views and "C" in views, (
        "Failed to extract the three sub-views from the (A | B) & C layout."
    )


def test_view_a_scatter_with_interval_brush(views):
    """View A must be a scatter of Horsepower vs MPG colored by Origin, with an x+y interval brush."""
    a = views["A"]
    assert _normalize_mark(a.get("mark")) == "point", (
        f"View A must use mark_point; got mark={a.get('mark')!r}."
    )
    enc = a.get("encoding") or {}
    assert enc.get("x", {}).get("field") == "Horsepower", (
        f"View A encoding.x.field must be 'Horsepower'; got {enc.get('x')!r}."
    )
    assert enc.get("y", {}).get("field") == "Miles_per_Gallon", (
        f"View A encoding.y.field must be 'Miles_per_Gallon'; got {enc.get('y')!r}."
    )
    # color may be wrapped inside a condition; first check the direct field
    color = enc.get("color") or {}
    color_field = color.get("field")
    if color_field is None and isinstance(color.get("condition"), dict):
        color_field = color["condition"].get("field")
    assert color_field == "Origin", (
        f"View A encoding.color.field must be 'Origin'; got {enc.get('color')!r}."
    )

    brush = _find_brush_param(a)
    assert brush is not None, (
        "View A must declare a selection_interval param whose `select.encodings` "
        "covers both 'x' and 'y' (i.e. an x+y interval brush attached via add_params)."
    )


def test_view_b_bar_filtered_by_brush(views):
    """View B must be a bar chart of count(*) by Origin, filtered by the brush from View A."""
    a, b = views["A"], views["B"]
    assert _normalize_mark(b.get("mark")) == "bar", (
        f"View B must use mark_bar; got mark={b.get('mark')!r}."
    )
    enc = b.get("encoding") or {}
    x_enc = enc.get("x") or {}
    y_enc = enc.get("y") or {}
    fields = {"x": x_enc.get("field"), "y": y_enc.get("field")}
    aggregates = {"x": x_enc.get("aggregate"), "y": y_enc.get("aggregate")}

    origin_channels = [ch for ch, fld in fields.items() if fld == "Origin"]
    assert len(origin_channels) == 1, (
        f"Exactly one of View B's x/y encodings must have field='Origin'; got {fields!r}."
    )
    other = "x" if origin_channels[0] == "y" else "y"
    assert aggregates[other] == "count", (
        f"The non-Origin axis of View B must use aggregate='count'; got {aggregates!r}."
    )

    brush = _find_brush_param(a)
    assert brush is not None, "Cannot validate View B's filter: View A is missing the brush param."
    brush_name = brush.get("name")
    assert brush_name, "View A's brush param must declare a 'name'."
    filters = _transform_filters_for_param(b, brush_name)
    assert filters, (
        f"View B must include a transform_filter referencing brush param "
        f"'{brush_name}' (e.g. {{'filter': {{'param': '{brush_name}'}}}})."
    )


def test_view_c_binned_heatmap_filtered_by_brush(views):
    """View C must be a 2D binned mark_rect heatmap colored by count(), filtered by the brush."""
    a, c = views["A"], views["C"]
    assert _normalize_mark(c.get("mark")) == "rect", (
        f"View C must use mark_rect; got mark={c.get('mark')!r}."
    )
    enc = c.get("encoding") or {}
    x_enc = enc.get("x") or {}
    y_enc = enc.get("y") or {}
    color_enc = enc.get("color") or {}

    assert x_enc.get("field") == "Weight_in_lbs", (
        f"View C encoding.x.field must be 'Weight_in_lbs'; got {x_enc!r}."
    )
    assert y_enc.get("field") == "Acceleration", (
        f"View C encoding.y.field must be 'Acceleration'; got {y_enc!r}."
    )
    assert x_enc.get("bin"), (
        f"View C encoding.x.bin must be truthy (binning enabled on x); got x={x_enc!r}."
    )
    assert y_enc.get("bin"), (
        f"View C encoding.y.bin must be truthy (binning enabled on y); got y={y_enc!r}."
    )
    assert color_enc.get("aggregate") == "count", (
        f"View C encoding.color.aggregate must be 'count'; got color={color_enc!r}."
    )

    brush = _find_brush_param(a)
    assert brush is not None, "Cannot validate View C's filter: View A is missing the brush param."
    brush_name = brush.get("name")
    assert brush_name, "View A's brush param must declare a 'name'."
    filters = _transform_filters_for_param(c, brush_name)
    assert filters, (
        f"View C must include a transform_filter referencing brush param "
        f"'{brush_name}' (e.g. {{'filter': {{'param': '{brush_name}'}}}})."
    )


# ----------------------------- browser check ---------------------------------


def test_browser_cross_filter_behavior(static_server):
    """Render chart.html in a real browser via pochi-verifier and check cross-filter behavior."""
    if PochiVerifier is None:
        pytest.skip("pochi-verifier is not installed in this environment.")
    verifier = PochiVerifier()
    reason = (
        "The page must render an Altair cross-filtering dashboard built on the cars dataset "
        "with three linked sub-views laid out as (left | right) over bottom: a scatter of "
        "Horsepower vs Miles_per_Gallon colored by Origin (top-left), a bar chart grouped by "
        "Origin (top-right), and a 2D binned heatmap of Weight_in_lbs vs Acceleration colored "
        "by count (bottom). Dragging an interval brush in the scatter view must cross-filter "
        "both the bar chart and the heatmap so they reflect only the brushed cars."
    )
    truth = (
        f"Navigate to {BASE_URL}/chart.html and wait for the Vega-Embed runtime to finish "
        "rendering. Confirm that three sub-plots are visible on the page, arranged with two "
        "plots side-by-side on top and one plot beneath them. The top-left view is a scatter "
        "plot of dots with axes labelled Horsepower (x) and Miles_per_Gallon (y) and dot color "
        "varying by Origin. The top-right view is a horizontal bar chart with a categorical "
        "axis showing Origin categories. The bottom view is a coloured rectangular grid "
        "(binned heatmap) whose axes are labelled with Weight_in_lbs and Acceleration. "
        "Then drag a rectangular brush across a sub-region of the scatter view; verify that "
        "the bar chart and the heatmap update so that only data inside the brushed region "
        "remains visible (cross-filtering behavior)."
    )
    result = verifier.verify(
        reason=reason,
        truth=truth,
        use_browser_agent=True,
        trajectory_dir="/logs/verifier/pochi/test_browser_cross_filter_behavior",
    )
    assert result.status == "pass", f"Browser verification failed: {result.reason}"
