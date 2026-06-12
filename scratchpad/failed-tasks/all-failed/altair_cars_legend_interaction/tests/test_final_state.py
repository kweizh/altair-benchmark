"""
Final-state verification for `altair_cars_legend_interaction`.

The executor must:
  - Build a (scatter | stacked_bar) & binned_histogram dashboard from the
    `cars` dataset.
  - Wire a SINGLE shared `selection_point(fields=['Origin'], bind='legend')`
    parameter, then use it to drive an `opacity` condition (≈ 1 selected vs.
    ≤ 0.5 unselected) in all three sub-views.
  - Save the result to `/home/user/myproject/chart.html`.

This module:
  1. Runs `python solution.py` to (re)build the artifact.
  2. Parses the embedded Vega-Lite spec from `chart.html`.
  3. Asserts layout, marks, encodings, selection wiring, and stacking rules.
  4. Uses `pochi-verifier` to confirm the interactive legend behavior in a
     real browser via a local HTTP server.
"""

import json
import os
import re
import socket
import subprocess
from typing import Any

import pytest
from xprocess import ProcessStarter

PROJECT_DIR = "/home/user/myproject"
SOLUTION_PATH = os.path.join(PROJECT_DIR, "solution.py")
CHART_HTML = os.path.join(PROJECT_DIR, "chart.html")
HTTP_PORT = 8765


# ---------------------------------------------------------------------------
# Spec extraction helpers
# ---------------------------------------------------------------------------

def _extract_balanced_json(text: str, start: int) -> str:
    """Return the JSON object starting at `text[start]` (which must be '{')."""
    assert text[start] == "{", "Expected JSON object start"
    depth = 0
    in_string = False
    escape = False
    i = start
    while i < len(text):
        ch = text[i]
        if in_string:
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == '"':
                in_string = False
        else:
            if ch == '"':
                in_string = True
            elif ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    return text[start : i + 1]
        i += 1
    raise ValueError("Unterminated JSON object while parsing chart.html")


def _extract_vega_lite_spec(html: str) -> dict:
    """Extract the Vega-Lite JSON spec embedded in an Altair-saved HTML file."""
    # Altair's default save template emits either a `var spec = {...};` literal
    # or an inline `vegaEmbed("#vis", {...}, {...})` call. Try both.
    patterns = [
        r"var\s+spec\s*=\s*",
        r"vegaEmbed\s*\(\s*[\"'][^\"']+[\"']\s*,\s*",
    ]
    for pattern in patterns:
        for match in re.finditer(pattern, html):
            json_start = match.end()
            # Skip whitespace until we hit '{'
            while json_start < len(html) and html[json_start] in " \t\r\n":
                json_start += 1
            if json_start < len(html) and html[json_start] == "{":
                blob = _extract_balanced_json(html, json_start)
                try:
                    return json.loads(blob)
                except json.JSONDecodeError:
                    continue
    raise AssertionError(
        "Could not locate a Vega-Lite spec in chart.html. "
        "Expected either `var spec = {...}` or `vegaEmbed(\"#vis\", {...}, ...)`."
    )


# ---------------------------------------------------------------------------
# Spec utility helpers
# ---------------------------------------------------------------------------

def _mark_type(mark: Any) -> str:
    if isinstance(mark, str):
        return mark
    if isinstance(mark, dict):
        return str(mark.get("type", ""))
    return ""


def _encoding(view: dict) -> dict:
    enc = view.get("encoding") or {}
    assert isinstance(enc, dict), f"View encoding must be a dict, got {type(enc)}"
    return enc


def _collect_params(spec: dict, *views: dict) -> list[dict]:
    """Collect parameters declared at the top-level and on any of the given views."""
    collected: list[dict] = []
    for container in (spec, *views):
        params = container.get("params") if isinstance(container, dict) else None
        if isinstance(params, list):
            for p in params:
                if isinstance(p, dict):
                    collected.append(p)
    return collected


def _find_legend_origin_param(params: list[dict]) -> dict | None:
    """Find a point-selection over `Origin` bound to a legend, if any."""
    for p in params:
        select = p.get("select")
        if not isinstance(select, dict):
            continue
        if select.get("type") != "point":
            continue
        fields = select.get("fields")
        if not isinstance(fields, list) or "Origin" not in fields:
            continue
        if select.get("bind") != "legend":
            continue
        return p
    return None


def _opacity_references_param(encoding: dict, param_name: str) -> tuple[bool, float, float]:
    """
    Return (references_param, selected_value, unselected_value).

    Accepts both forms:
      - {"condition": {"param": <name>, "value": 1}, "value": 0.15}
      - {"condition": {"test": "<expr mentioning name>", "value": 1}, "value": 0.15}
      - condition can also be a list of dicts.
    """
    opacity = encoding.get("opacity")
    if not isinstance(opacity, dict):
        return (False, 0.0, 1.0)

    condition = opacity.get("condition")
    otherwise_value = opacity.get("value")

    candidates: list[dict] = []
    if isinstance(condition, dict):
        candidates.append(condition)
    elif isinstance(condition, list):
        for c in condition:
            if isinstance(c, dict):
                candidates.append(c)

    matched = None
    for c in candidates:
        if c.get("param") == param_name:
            matched = c
            break
        test = c.get("test")
        if isinstance(test, str) and param_name in test:
            matched = c
            break
    if matched is None:
        return (False, 0.0, 1.0)

    def _coerce(value: Any, default: float) -> float:
        try:
            return float(value)
        except (TypeError, ValueError):
            return default

    selected_value = _coerce(matched.get("value"), 1.0)
    unselected_value = _coerce(otherwise_value, 1.0)
    return (True, selected_value, unselected_value)


# ---------------------------------------------------------------------------
# Build / parse fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def built_spec() -> dict:
    """Run solution.py and parse the resulting Vega-Lite spec."""
    assert os.path.isfile(SOLUTION_PATH), (
        f"solution.py is missing at {SOLUTION_PATH}; cannot run executor entry point."
    )
    # Clean stale artifact so we know we're testing the freshly built one.
    if os.path.exists(CHART_HTML):
        os.remove(CHART_HTML)

    result = subprocess.run(
        ["python", "solution.py"],
        cwd=PROJECT_DIR,
        capture_output=True,
        text=True,
        timeout=180,
    )
    assert result.returncode == 0, (
        f"`python solution.py` exited with {result.returncode}. "
        f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
    )
    assert os.path.isfile(CHART_HTML), (
        f"Expected `solution.py` to produce {CHART_HTML}, but it was not created."
    )
    assert os.path.getsize(CHART_HTML) > 0, f"{CHART_HTML} is empty."

    with open(CHART_HTML, "r", encoding="utf-8") as f:
        html = f.read()
    spec = _extract_vega_lite_spec(html)
    assert isinstance(spec, dict), "Extracted Vega-Lite spec must be a JSON object."
    return spec


@pytest.fixture(scope="session")
def views(built_spec: dict) -> dict:
    """Resolve the three sub-views A, B, C from the composed spec."""
    vconcat = built_spec.get("vconcat")
    assert isinstance(vconcat, list) and len(vconcat) == 2, (
        f"Top-level spec must have a `vconcat` of length 2. Got: {type(vconcat).__name__} "
        f"len={len(vconcat) if isinstance(vconcat, list) else 'N/A'}."
    )
    top_row = vconcat[0]
    assert isinstance(top_row, dict), "First entry of `vconcat` must be an object."
    hconcat = top_row.get("hconcat")
    assert isinstance(hconcat, list) and len(hconcat) == 2, (
        "vconcat[0] must be an `hconcat` of exactly 2 sub-views (scatter | stacked_bar)."
    )
    view_a = hconcat[0]
    view_b = hconcat[1]
    view_c = vconcat[1]
    assert isinstance(view_a, dict), "View A must be an object."
    assert isinstance(view_b, dict), "View B must be an object."
    assert isinstance(view_c, dict), "View C must be an object."
    return {"A": view_a, "B": view_b, "C": view_c}


@pytest.fixture(scope="session")
def legend_param_name(built_spec: dict, views: dict) -> str:
    """Locate the unique legend-bound `Origin` selection parameter name."""
    all_params = _collect_params(built_spec, views["A"], views["B"], views["C"])
    assert all_params, (
        "No `params` declared anywhere in the spec; expected a "
        "`selection_point(fields=['Origin'], bind='legend')` parameter."
    )
    matching = [p for p in all_params if _find_legend_origin_param([p]) is not None]
    assert matching, (
        "Did not find a point-selection parameter with fields containing 'Origin' "
        "and bind='legend'. The dashboard must declare exactly one shared "
        "legend-bound selection over `Origin`."
    )
    unique_names = {p.get("name") for p in matching if isinstance(p.get("name"), str)}
    assert len(unique_names) == 1, (
        "The dashboard must declare exactly one logical shared legend selection; "
        f"found these parameter names instead: {unique_names}."
    )
    name = next(iter(unique_names))
    assert isinstance(name, str) and name, "The shared selection must have a non-empty `name`."
    return name


# ---------------------------------------------------------------------------
# Spec-level assertions
# ---------------------------------------------------------------------------

def test_chart_html_exists(built_spec: dict):
    """solution.py must produce a non-empty chart.html."""
    assert os.path.isfile(CHART_HTML), f"chart.html missing at {CHART_HTML}."
    assert built_spec, "Parsed Vega-Lite spec is empty."


def test_layout_is_vconcat_of_hconcat_and_view(views: dict):
    """Top-level layout must be `(A | B) & C`."""
    # The `views` fixture already enforces the structural shape.
    assert set(views.keys()) == {"A", "B", "C"}


def test_view_a_scatter(views: dict, legend_param_name: str):
    """View A: scatter of Horsepower vs Miles_per_Gallon colored by Origin."""
    a = views["A"]
    mark = _mark_type(a.get("mark"))
    assert mark in {"point", "circle"}, (
        f"View A mark must be 'point' or 'circle', got {mark!r}."
    )
    enc = _encoding(a)
    x_field = (enc.get("x") or {}).get("field")
    y_field = (enc.get("y") or {}).get("field")
    color_field = (enc.get("color") or {}).get("field")
    assert x_field == "Horsepower", f"View A x.field must be 'Horsepower', got {x_field!r}."
    assert y_field == "Miles_per_Gallon", (
        f"View A y.field must be 'Miles_per_Gallon', got {y_field!r}."
    )
    assert color_field == "Origin", f"View A color.field must be 'Origin', got {color_field!r}."

    referenced, sel_val, unsel_val = _opacity_references_param(enc, legend_param_name)
    assert referenced, (
        f"View A must encode `opacity` via a conditional encoding referencing the "
        f"shared selection param {legend_param_name!r}."
    )
    assert sel_val >= 0.9, (
        f"View A selected-opacity value must be ≈ 1, got {sel_val} for selection {legend_param_name!r}."
    )
    assert unsel_val <= 0.5, (
        f"View A unselected-opacity value must be ≤ 0.5 (a visible dim), got {unsel_val}."
    )


def test_view_b_stacked_bar(views: dict, legend_param_name: str):
    """View B: stacked bar of count by Cylinders:O colored by Origin (no xOffset)."""
    b = views["B"]
    mark = _mark_type(b.get("mark"))
    assert mark == "bar", f"View B mark must be 'bar', got {mark!r}."

    enc = _encoding(b)
    x = enc.get("x") or {}
    y = enc.get("y") or {}
    color = enc.get("color") or {}

    assert x.get("field") == "Cylinders", (
        f"View B x.field must be 'Cylinders', got {x.get('field')!r}."
    )
    assert x.get("type") == "ordinal", (
        f"View B x.type must be 'ordinal' (use `Cylinders:O`), got {x.get('type')!r}."
    )
    assert y.get("aggregate") == "count", (
        f"View B y.aggregate must be 'count', got {y.get('aggregate')!r}."
    )
    assert color.get("field") == "Origin", (
        f"View B color.field must be 'Origin', got {color.get('field')!r}."
    )
    assert "xOffset" not in enc, (
        "View B must be a STACKED bar chart, not a grouped one — "
        "the spec must not declare an `xOffset` encoding."
    )

    referenced, sel_val, unsel_val = _opacity_references_param(enc, legend_param_name)
    assert referenced, (
        f"View B must encode `opacity` via a conditional encoding referencing the "
        f"shared selection param {legend_param_name!r}."
    )
    assert sel_val >= 0.9, (
        f"View B selected-opacity value must be ≈ 1, got {sel_val}."
    )
    assert unsel_val <= 0.5, (
        f"View B unselected-opacity value must be ≤ 0.5, got {unsel_val}."
    )


def test_view_c_binned_histogram(views: dict, legend_param_name: str):
    """View C: histogram of Acceleration (binned) colored by Origin."""
    c = views["C"]
    mark = _mark_type(c.get("mark"))
    assert mark == "bar", f"View C mark must be 'bar', got {mark!r}."

    enc = _encoding(c)
    x = enc.get("x") or {}
    y = enc.get("y") or {}
    color = enc.get("color") or {}

    assert x.get("field") == "Acceleration", (
        f"View C x.field must be 'Acceleration', got {x.get('field')!r}."
    )
    assert x.get("bin"), (
        f"View C x.bin must be truthy (use Altair's `.bin()`), got {x.get('bin')!r}."
    )
    assert y.get("aggregate") == "count", (
        f"View C y.aggregate must be 'count', got {y.get('aggregate')!r}."
    )
    assert color.get("field") == "Origin", (
        f"View C color.field must be 'Origin', got {color.get('field')!r}."
    )

    referenced, sel_val, unsel_val = _opacity_references_param(enc, legend_param_name)
    assert referenced, (
        f"View C must encode `opacity` via a conditional encoding referencing the "
        f"shared selection param {legend_param_name!r}."
    )
    assert sel_val >= 0.9, (
        f"View C selected-opacity value must be ≈ 1, got {sel_val}."
    )
    assert unsel_val <= 0.5, (
        f"View C unselected-opacity value must be ≤ 0.5, got {unsel_val}."
    )


# ---------------------------------------------------------------------------
# Browser verification
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def start_http_server(xprocess, built_spec):
    """Serve /home/user/myproject on HTTP_PORT for browser verification."""

    class Starter(ProcessStarter):
        name = "altair_legend_static_server"
        args = ["python", "-m", "http.server", str(HTTP_PORT)]
        env = os.environ.copy()
        popen_kwargs = {
            "cwd": PROJECT_DIR,
            "text": True,
        }
        timeout = 60
        terminate_on_interrupt = True

        def startup_check(self):
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                return s.connect_ex(("localhost", HTTP_PORT)) == 0

    xprocess.ensure(Starter.name, Starter)
    yield f"http://localhost:{HTTP_PORT}/chart.html"
    info = xprocess.getinfo(Starter.name)
    info.terminate()


def test_browser_legend_interaction(start_http_server):
    """Browser-level confirmation that the shared legend selection works."""
    from pochi_verifier import PochiVerifier

    url = start_http_server
    reason = (
        "The chart must render three linked sub-views of the cars dataset — a "
        "Horsepower vs Miles_per_Gallon scatter, a stacked bar of count by "
        "Cylinders, and a binned histogram of Acceleration — all colored by "
        "Origin. A single Origin legend must be clickable and drive opacity in "
        "every sub-view: clicking one origin keeps that origin's marks bright "
        "while dimming the other origins across ALL three charts simultaneously."
    )
    truth = (
        f"Navigate to {url} and wait for the Vega-embed runtime to finish "
        "rendering (canvas or SVG marks visible). Confirm that THREE separate "
        "sub-views are visible on the page in a `(top-left | top-right) over "
        "bottom` arrangement: a Horsepower vs Miles_per_Gallon scatter on the "
        "top-left, a stacked bar chart of count by Cylinders on the top-right, "
        "and a binned histogram of Acceleration along the bottom. Confirm that "
        "an `Origin` color legend is rendered with the three origins (e.g. "
        "USA, Europe, Japan) and that legend entries are clickable. Click ONE "
        "Origin legend entry (e.g. 'Japan') and verify that, in ALL THREE "
        "sub-views simultaneously, the marks for that origin remain fully "
        "opaque/saturated while the marks for the other two origins become "
        "visibly dimmer (lower opacity). Click the same legend entry again (or "
        "click empty space in the legend) and verify that every mark in all "
        "three sub-views returns to full opacity. The highlight/dim effect "
        "must be driven by a SINGLE shared legend selection, not by separate "
        "per-chart controls."
    )

    verifier = PochiVerifier()
    result = verifier.verify(
        reason=reason,
        truth=truth,
        use_browser_agent=True,
        trajectory_dir="/logs/verifier/pochi/test_browser_legend_interaction",
    )
    assert result.status == "pass", (
        f"Browser verification failed: {getattr(result, 'reason', result)}"
    )
