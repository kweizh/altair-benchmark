"""Final-state verification for `altair_unemployment_streamgraph`.

Re-runs the agent's solution from a clean state, then inspects the resulting
HTML for:
  1. A self-contained Vega-Lite specification embedded via `vegaEmbed(...)`.
  2. The required encodings, marks, selection, and window-rank transform.
  3. Browser rendering of the streamgraph and hover overlay via pochi-verifier.
"""

import json
import os
import re
import socket
import subprocess
from typing import Any, Iterable

import pytest
from pochi_verifier import PochiVerifier
from xprocess import ProcessStarter

PROJECT_DIR = "/home/user/myproject"
SOLUTION_FILE = os.path.join(PROJECT_DIR, "solution.py")
OUTPUT_DIR = os.path.join(PROJECT_DIR, "out")
CHART_HTML = os.path.join(OUTPUT_DIR, "chart.html")
SERVE_PORT = 8765


# ---------------------------------------------------------------------------
# Spec-extraction helpers
# ---------------------------------------------------------------------------


def _extract_spec_from_html(html: str) -> dict:
    """Extract the Vega-Lite JSON spec embedded in an Altair-saved HTML file."""
    # Altair's default HTML template includes a call of the form
    #   vegaEmbed("#vis", {spec...}, embedOpt).then(...)
    # We locate the first balanced JSON object passed as the 2nd argument.
    match = re.search(r"vegaEmbed\s*\(\s*[^,]+,\s*", html)
    assert match, "Could not find vegaEmbed(...) call in HTML."
    start = match.end()
    # Walk forward to find the balanced JSON object beginning with '{'.
    while start < len(html) and html[start] != "{":
        start += 1
    assert start < len(html), "Could not locate opening '{' after vegaEmbed(...,"
    depth = 0
    in_str = False
    escape = False
    end = start
    while end < len(html):
        ch = html[end]
        if in_str:
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == '"':
                in_str = False
        else:
            if ch == '"':
                in_str = True
            elif ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    end += 1
                    break
        end += 1
    assert depth == 0, "Unbalanced braces while extracting vegaEmbed spec."
    raw = html[start:end]
    return json.loads(raw)


def _iter_views(spec: Any) -> Iterable[dict]:
    """Yield every view-like dict in the spec (top-level + nested layers/concats)."""
    if isinstance(spec, dict):
        yield spec
        for key in ("layer", "hconcat", "vconcat", "concat", "spec"):
            child = spec.get(key)
            if isinstance(child, list):
                for c in child:
                    yield from _iter_views(c)
            elif isinstance(child, dict):
                yield from _iter_views(child)


def _mark_obj(view: dict) -> dict:
    """Normalise a view's 'mark' field into a dict with a 'type' key."""
    mark = view.get("mark")
    if isinstance(mark, str):
        return {"type": mark}
    if isinstance(mark, dict):
        return mark
    return {}


def _collect_params(spec: dict) -> list[dict]:
    params: list[dict] = []
    for view in _iter_views(spec):
        p = view.get("params")
        if isinstance(p, list):
            params.extend([x for x in p if isinstance(x, dict)])
    return params


def _iter_transforms(spec: dict) -> Iterable[dict]:
    for view in _iter_views(spec):
        tx = view.get("transform")
        if isinstance(tx, list):
            for entry in tx:
                if isinstance(entry, dict):
                    yield entry


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def run_solution():
    """Execute the agent's solution from a clean state."""
    assert os.path.isfile(SOLUTION_FILE), (
        f"Expected agent to create entry point at {SOLUTION_FILE}."
    )
    if os.path.exists(CHART_HTML):
        os.remove(CHART_HTML)
    result = subprocess.run(
        ["python3", "solution.py"],
        cwd=PROJECT_DIR,
        capture_output=True,
        text=True,
        timeout=180,
    )
    return result


@pytest.fixture(scope="module")
def chart_spec(run_solution):
    assert run_solution.returncode == 0, (
        "python3 solution.py exited non-zero.\n"
        f"stdout={run_solution.stdout!r}\nstderr={run_solution.stderr!r}"
    )
    assert os.path.isfile(CHART_HTML), (
        f"Expected solution to write {CHART_HTML}."
    )
    with open(CHART_HTML, encoding="utf-8") as f:
        html = f.read()
    assert html.strip(), f"{CHART_HTML} is empty."
    spec = _extract_spec_from_html(html)
    assert isinstance(spec, dict) and spec, "Extracted Vega-Lite spec is empty."
    return spec


@pytest.fixture(scope="session")
def browser_verifier():
    yield PochiVerifier()


@pytest.fixture(scope="session")
def serve_chart(xprocess):
    """Serve the project directory over HTTP so the chart loads in a browser."""

    class Starter(ProcessStarter):
        name = "serve_chart"
        args = ["python3", "-m", "http.server", str(SERVE_PORT)]
        env = os.environ.copy()
        popen_kwargs = {"cwd": OUTPUT_DIR, "text": True}
        timeout = 60
        terminate_on_interrupt = True

        def startup_check(self):
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                return s.connect_ex(("localhost", SERVE_PORT)) == 0

    # Ensure the output directory exists before serving (the run_solution
    # fixture has session scope through chart_spec usage in tests below).
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    xprocess.ensure(Starter.name, Starter)
    yield f"http://localhost:{SERVE_PORT}/chart.html"
    info = xprocess.getinfo(Starter.name)
    info.terminate()


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_solution_runs_successfully(run_solution):
    assert run_solution.returncode == 0, (
        "python3 solution.py failed.\n"
        f"stdout={run_solution.stdout!r}\nstderr={run_solution.stderr!r}"
    )


def test_chart_html_exists_and_nonempty(run_solution):
    assert os.path.isfile(CHART_HTML), (
        f"Expected solution to write {CHART_HTML} after execution."
    )
    assert os.path.getsize(CHART_HTML) > 0, f"{CHART_HTML} is empty."


def test_area_layer_with_monotone_interpolate(chart_spec):
    area_views = [v for v in _iter_views(chart_spec) if _mark_obj(v).get("type") == "area"]
    assert area_views, "No layer with mark.type == 'area' found in the spec."
    matching = [v for v in area_views if _mark_obj(v).get("interpolate") == "monotone"]
    assert matching, (
        "No 'area' layer with `interpolate: \"monotone\"` found. "
        f"Found area marks: {[_mark_obj(v) for v in area_views]}"
    )


def test_area_layer_center_stacked_sum_count(chart_spec):
    for view in _iter_views(chart_spec):
        if _mark_obj(view).get("type") != "area":
            continue
        enc = view.get("encoding") or {}
        y = enc.get("y") or {}
        if (
            y.get("aggregate") == "sum"
            and y.get("field") == "count"
            and y.get("stack") == "center"
        ):
            return
    pytest.fail(
        "No area layer's Y encoding satisfies aggregate=='sum', field=='count', stack=='center'."
    )


def test_area_layer_x_yearmonth_date(chart_spec):
    for view in _iter_views(chart_spec):
        if _mark_obj(view).get("type") != "area":
            continue
        enc = view.get("encoding") or {}
        x = enc.get("x") or {}
        if (
            x.get("timeUnit") == "yearmonth"
            and x.get("field") == "date"
            and x.get("type") == "temporal"
        ):
            return
    pytest.fail(
        "No area layer's X encoding satisfies timeUnit=='yearmonth', field=='date', type=='temporal'."
    )


def test_area_layer_color_series_category20b(chart_spec):
    for view in _iter_views(chart_spec):
        if _mark_obj(view).get("type") != "area":
            continue
        enc = view.get("encoding") or {}
        color = enc.get("color") or {}
        if color.get("field") != "series":
            continue
        scale = color.get("scale") or {}
        if scale.get("scheme") == "category20b":
            return
    pytest.fail(
        "Area layer's color encoding must use field 'series' with a 'category20b' scheme."
    )


def test_nearest_pointerover_selection_point(chart_spec):
    params = _collect_params(chart_spec)
    point_params = [p for p in params if (p.get("select") or {}).get("type") == "point"]
    # Also allow shorthand where param's own 'type' is 'point' if 'select' is a dict.
    candidates = []
    for p in params:
        sel = p.get("select")
        if not isinstance(sel, dict):
            continue
        if sel.get("type") != "point":
            continue
        candidates.append((p, sel))
    assert candidates, (
        f"No `selection_point` (`select.type == 'point'`) param found. "
        f"Params seen: {params}"
    )
    for p, sel in candidates:
        on_value = sel.get("on")
        on_str = on_value if isinstance(on_value, str) else json.dumps(on_value)
        if not ("pointerover" in on_str or "mouseover" in on_str):
            continue
        if sel.get("nearest") is not True:
            continue
        encs = sel.get("encodings") or []
        if "x" not in encs:
            continue
        if sel.get("empty") is not False:
            continue
        return
    pytest.fail(
        "No selection_point matches required configuration: "
        "on contains 'pointerover'/'mouseover', nearest=True, encodings includes 'x', empty=False. "
        f"Candidates: {[sel for _, sel in candidates]}"
    )


def test_rule_layer_bound_to_selection(chart_spec):
    """At least one rule mark layer must depend on the hover selection."""
    params = _collect_params(chart_spec)
    point_param_names = {
        p["name"]
        for p in params
        if isinstance(p.get("name"), str)
        and isinstance(p.get("select"), dict)
        and (p["select"].get("type") == "point")
    }
    assert point_param_names, "No named point selection params found."

    rule_views = [v for v in _iter_views(chart_spec) if _mark_obj(v).get("type") == "rule"]
    assert rule_views, "No layer with mark.type == 'rule' found in the spec."

    def refs_selection(node: Any) -> bool:
        if isinstance(node, dict):
            param_ref = node.get("param")
            if isinstance(param_ref, str) and param_ref in point_param_names:
                return True
            for v in node.values():
                if refs_selection(v):
                    return True
        elif isinstance(node, list):
            for item in node:
                if refs_selection(item):
                    return True
        return False

    for rule in rule_views:
        if refs_selection(rule.get("encoding") or {}):
            return
        if refs_selection(rule):
            return
    pytest.fail(
        "No rule-mark layer references the hover selection param "
        f"({sorted(point_param_names)}) via a condition."
    )


def test_text_layer_present(chart_spec):
    text_views = [v for v in _iter_views(chart_spec) if _mark_obj(v).get("type") == "text"]
    assert text_views, "No layer with mark.type == 'text' found in the spec."


def test_window_rank_groupby_date(chart_spec):
    """A transform_window with rank op, groupby date, sort by count desc must exist."""
    matched = False
    for tx in _iter_transforms(chart_spec):
        window = tx.get("window")
        if not isinstance(window, list):
            continue
        has_rank = any(
            isinstance(w, dict) and w.get("op") == "rank" for w in window
        )
        if not has_rank:
            continue
        groupby = tx.get("groupby") or []
        if "date" not in groupby:
            continue
        sort = tx.get("sort") or []
        sort_ok = any(
            isinstance(s, dict)
            and s.get("field") == "count"
            and (s.get("order") == "descending")
            for s in sort
        )
        if not sort_ok:
            continue
        matched = True
        break
    assert matched, (
        "Expected a `transform_window` with op='rank', groupby including 'date', "
        "and sort by 'count' descending."
    )


def test_streamgraph_renders_in_browser(serve_chart, browser_verifier):
    chart_url = serve_chart
    reason = (
        "The HTML should render an interactive Altair streamgraph of US "
        "unemployment counts across industries. Industry bands must be "
        "vertically stacked around a central baseline (center stack, "
        "streamgraph shape) and colored by industry. Moving the pointer "
        "horizontally must reveal a vertical ruler at the nearest month and "
        "a text annotation showing the dominant industry for that month."
    )
    truth = f"""
1. Open a browser tab and navigate to {chart_url}.
2. Wait for the chart to render. Confirm a streamgraph appears: multiple
   coloured industry bands stacked symmetrically around a horizontal centerline
   (i.e., the bands extend both above and below a central baseline, not from a
   y=0 baseline). The X axis spans roughly 2000-2010 (yearmonth ticks).
3. Move the mouse pointer horizontally across the chart area at mid-height.
   Confirm that a vertical ruler line appears at the position of the pointer
   and tracks the nearest month as the pointer moves.
4. While hovering, confirm that a text label (the top industry name for that
   month, such as "Government", "Manufacturing", "Trade Transportation Utilities",
   etc.) is shown near the ruler, and that the label updates as you move the
   pointer to different months.
"""
    result = browser_verifier.verify(
        reason=reason,
        truth=truth,
        use_browser_agent=True,
        trajectory_dir="/logs/verifier/pochi/test_streamgraph_renders_in_browser",
    )
    assert result.status == "pass", f"Browser verification failed: {result.reason}"
