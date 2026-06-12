import json
import os
import re
import socket
import subprocess

import pytest
from xprocess import ProcessStarter

from pochi_verifier import PochiVerifier


PROJECT_DIR = "/home/user/myproject"
CHART_HTML = os.path.join(PROJECT_DIR, "chart.html")
BUILD_SCRIPT = os.path.join(PROJECT_DIR, "build_chart.py")
EXPECTED_SYMBOLS = ["MSFT", "AMZN", "IBM", "GOOG", "AAPL"]
SERVER_PORT = 8765


# ---------------------------------------------------------------------------
# Spec extraction helpers
# ---------------------------------------------------------------------------


def _extract_json_object(text: str, start_idx: int) -> dict:
    """Extract a balanced JSON object literal starting at the first ``{`` at or
    after ``start_idx``."""
    while start_idx < len(text) and text[start_idx] != "{":
        start_idx += 1
    assert start_idx < len(text), "Could not locate a JSON object in chart HTML."
    depth = 0
    in_string = False
    escape = False
    end_idx = None
    for i in range(start_idx, len(text)):
        ch = text[i]
        if in_string:
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == '"':
                in_string = False
            continue
        if ch == '"':
            in_string = True
        elif ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                end_idx = i + 1
                break
    assert end_idx is not None, "Failed to balance braces while extracting spec."
    return json.loads(text[start_idx:end_idx])


def _load_spec_from_html(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        html = f.read()
    markers = ["var spec = ", "const spec = ", "let spec = "]
    for marker in markers:
        idx = html.find(marker)
        if idx >= 0:
            return _extract_json_object(html, idx + len(marker))
    # Fallback: parse the first JSON object literal passed to vegaEmbed(...).
    idx = html.find("vegaEmbed(")
    assert idx >= 0, "chart.html does not appear to be an Altair/Vega-Embed export."
    # Skip past the element selector argument (string literal).
    return _extract_json_object(html, idx + len("vegaEmbed("))


def _walk(spec):
    """Yield every dict node in the spec tree."""
    if isinstance(spec, dict):
        yield spec
        for v in spec.values():
            yield from _walk(v)
    elif isinstance(spec, list):
        for v in spec:
            yield from _walk(v)


def _collect_layers(spec: dict):
    """Return the list of layer dicts in a layered top-level spec."""
    assert isinstance(spec, dict), "Spec is not a JSON object."
    assert "layer" in spec and isinstance(spec["layer"], list), (
        "Top-level spec must be a layered chart with a 'layer' array."
    )
    return spec["layer"]


# ---------------------------------------------------------------------------
# Fixtures: (re)build the chart, then serve it on a local HTTP server.
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def built_chart():
    """Rebuild the chart artifact by running the agent's build script."""
    assert os.path.isfile(BUILD_SCRIPT), (
        f"Expected build script at {BUILD_SCRIPT} but it was not found."
    )
    if os.path.exists(CHART_HTML):
        os.remove(CHART_HTML)
    result = subprocess.run(
        ["python3", BUILD_SCRIPT],
        capture_output=True,
        text=True,
        cwd=PROJECT_DIR,
    )
    assert result.returncode == 0, (
        f"build_chart.py exited non-zero.\nstdout:\n{result.stdout}\n"
        f"stderr:\n{result.stderr}"
    )
    assert os.path.isfile(CHART_HTML), (
        f"Expected build_chart.py to create {CHART_HTML}, but it does not exist."
    )
    return CHART_HTML


@pytest.fixture(scope="session")
def spec(built_chart):
    return _load_spec_from_html(built_chart)


@pytest.fixture(scope="session")
def static_server(built_chart, xprocess):
    """Serve PROJECT_DIR over HTTP so the browser verifier can fetch chart.html."""

    class Starter(ProcessStarter):
        name = "altair_chart_server"
        args = ["python3", "-m", "http.server", str(SERVER_PORT)]
        env = os.environ.copy()
        popen_kwargs = {"cwd": PROJECT_DIR, "text": True}
        timeout = 30
        terminate_on_interrupt = True

        def startup_check(self):
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                return s.connect_ex(("localhost", SERVER_PORT)) == 0

    xprocess.ensure(Starter.name, Starter)
    yield f"http://localhost:{SERVER_PORT}/chart.html"
    info = xprocess.getinfo(Starter.name)
    info.terminate()


@pytest.fixture(scope="session")
def browser_verifier():
    return PochiVerifier()


# ---------------------------------------------------------------------------
# Spec-level tests
# ---------------------------------------------------------------------------


def test_chart_html_created(built_chart):
    """build_chart.py must regenerate the chart artifact."""
    assert os.path.isfile(built_chart), f"{built_chart} was not produced."


def test_layered_with_at_least_three_layers(spec):
    layers = _collect_layers(spec)
    assert len(layers) >= 3, (
        f"Expected the top-level chart to have at least 3 layers, got {len(layers)}."
    )


def _find_window_transform(layer: dict):
    for t in layer.get("transform", []) or []:
        if isinstance(t, dict) and "window" in t:
            return t
    return None


def test_rolling_window_layer(spec):
    """Exactly one layer must compute a 30-day centered rolling mean of price by symbol."""
    layers = _collect_layers(spec)
    matches = []
    for layer in layers:
        wt = _find_window_transform(layer)
        if wt is None:
            continue
        window_fields = wt.get("window") or []
        # The window field-def list must contain mean(price) with a non-empty alias.
        mean_price_aliases = [
            wf.get("as")
            for wf in window_fields
            if isinstance(wf, dict)
            and wf.get("op") == "mean"
            and wf.get("field") == "price"
            and wf.get("as")
        ]
        if not mean_price_aliases:
            continue
        groupby = wt.get("groupby") or []
        if groupby != ["symbol"]:
            continue
        frame = wt.get("frame")
        # Accept any 2-element frame whose absolute extents are 15.
        if not (isinstance(frame, list) and len(frame) == 2):
            continue
        a, b = frame
        if not (isinstance(a, (int, float)) and isinstance(b, (int, float))):
            continue
        if not (abs(a) == 15 and abs(b) == 15 and a < 0 < b or (a == -15 and b == 15)):
            continue
        # The mark of the layer must be a line, and one of the alias names must be
        # referenced on the y-channel encoding.
        mark = layer.get("mark")
        mark_type = mark if isinstance(mark, str) else (mark or {}).get("type")
        if mark_type != "line":
            continue
        y_enc = (layer.get("encoding") or {}).get("y") or {}
        y_field = y_enc.get("field") if isinstance(y_enc, dict) else None
        if y_field in mean_price_aliases:
            matches.append(layer)
    assert len(matches) >= 1, (
        "Expected one layer to define a window transform with op=mean field=price, "
        "groupby=['symbol'], a centered 30-day frame [-15, 15], a line mark, and a "
        "y-encoding bound to the rolling-mean alias."
    )


def _find_joinaggregate_transform(layer: dict):
    for t in layer.get("transform", []) or []:
        if isinstance(t, dict) and "joinaggregate" in t:
            return t
    return None


def test_joinaggregate_reference_rule_layer(spec):
    """A dashed per-symbol horizontal mean-price rule layer must exist, fed by a
    joinaggregate(mean(price)) groupby=['symbol']."""
    # Gather every joinaggregate transform in the spec tree, and the mean(price)
    # output aliases they produce when grouped by 'symbol'.
    mean_aliases: list[str] = []
    for node in _walk(spec):
        for t in node.get("transform", []) or []:
            if not isinstance(t, dict) or "joinaggregate" not in t:
                continue
            if (t.get("groupby") or []) != ["symbol"]:
                continue
            for jf in t.get("joinaggregate") or []:
                if (
                    isinstance(jf, dict)
                    and jf.get("op") == "mean"
                    and jf.get("field") == "price"
                    and jf.get("as")
                ):
                    mean_aliases.append(jf["as"])
    assert mean_aliases, (
        "Expected a transform_joinaggregate with op=mean field=price "
        "groupby=['symbol'] somewhere in the spec."
    )

    # Find at least one rule-mark layer whose mark uses strokeDash and whose y
    # encoding is bound to one of those join-aggregate aliases.
    layers = _collect_layers(spec)
    matches = []
    for layer in layers:
        mark = layer.get("mark")
        mark_type = mark if isinstance(mark, str) else (mark or {}).get("type")
        if mark_type != "rule":
            continue
        mark_obj = mark if isinstance(mark, dict) else {}
        if "strokeDash" not in mark_obj:
            continue
        y_enc = (layer.get("encoding") or {}).get("y") or {}
        y_field = y_enc.get("field") if isinstance(y_enc, dict) else None
        if y_field in mean_aliases:
            matches.append(layer)
    assert matches, (
        "Expected at least one rule-mark layer with a strokeDash and a y-encoding "
        "bound to the per-symbol mean(price) joinaggregate alias."
    )


def _collect_params(spec: dict):
    """Collect every params entry anywhere in the spec tree."""
    params = []
    for node in _walk(spec):
        for p in node.get("params", []) or []:
            if isinstance(p, dict):
                params.append(p)
    return params


def test_dropdown_param_with_five_symbols(spec):
    """A params entry must be bound to a select input with the 5 expected symbols."""
    params = _collect_params(spec)
    matching = []
    for p in params:
        bind = p.get("bind")
        if not isinstance(bind, dict):
            continue
        if bind.get("input") != "select":
            continue
        opts = bind.get("options")
        if opts == EXPECTED_SYMBOLS:
            matching.append(p)
    assert len(matching) >= 1, (
        "Expected a params entry whose bind is "
        "{'input': 'select', 'options': ['MSFT', 'AMZN', 'IBM', 'GOOG', 'AAPL']}, "
        f"but found params: {[p.get('bind') for p in params]}"
    )


def test_filter_references_dropdown_param(spec):
    """A transform_filter must reference the dropdown parameter."""
    params = _collect_params(spec)
    dropdown_names = [
        p.get("name")
        for p in params
        if isinstance(p.get("bind"), dict)
        and p["bind"].get("input") == "select"
        and p["bind"].get("options") == EXPECTED_SYMBOLS
    ]
    assert dropdown_names, "No dropdown parameter found to reference in a filter."

    filters = []
    for node in _walk(spec):
        for t in node.get("transform", []) or []:
            if isinstance(t, dict) and "filter" in t:
                filters.append(t["filter"])

    def _references_dropdown(filter_clause) -> bool:
        if isinstance(filter_clause, dict):
            if "param" in filter_clause and filter_clause["param"] in dropdown_names:
                return True
            # Composed predicates (and/or/not) — walk recursively.
            for v in filter_clause.values():
                if isinstance(v, (dict, list)) and _references_dropdown(v):
                    return True
        elif isinstance(filter_clause, list):
            return any(_references_dropdown(v) for v in filter_clause)
        elif isinstance(filter_clause, str):
            return any(name in filter_clause for name in dropdown_names)
        return False

    assert any(_references_dropdown(f) for f in filters), (
        "Expected a transform_filter that references the dropdown parameter "
        f"({dropdown_names}), but no such filter was found. Filters seen: {filters}"
    )


def test_interactive_scales_selection(spec):
    """`.interactive()` must add an interval-bound-to-scales selection."""
    params = _collect_params(spec)
    interval_scales = [
        p
        for p in params
        if isinstance(p.get("select"), dict)
        and p["select"].get("type") == "interval"
        and p.get("bind") == "scales"
    ]
    assert interval_scales, (
        "Expected a params entry with select.type == 'interval' and bind == 'scales' "
        "(produced by chart.interactive()), but none was found. "
        f"Params seen: {params}"
    )


# ---------------------------------------------------------------------------
# Browser verification
# ---------------------------------------------------------------------------


def test_browser_renders_lines_dashed_rule_and_dropdown(
    spec, static_server, browser_verifier
):
    """Render chart.html in a browser and confirm visible lines, dashed rule, and dropdown."""
    url = static_server
    reason = (
        "The Altair-exported chart.html must render an interactive layered "
        "multi-company stock chart with raw and rolling-mean lines, a dashed "
        "per-symbol mean-price reference rule, and a dropdown widget that "
        "filters which symbol is displayed."
    )
    truth = (
        f"Navigate to {url} and wait until the Vega-Embed visualization has finished "
        "loading (no error message is shown in the chart container). Verify all of "
        "the following are true: (1) at least two SVG path or canvas-drawn line "
        "marks are visible in the chart area; (2) at least one mark in the chart "
        "uses a dashed stroke (its SVG stroke-dasharray attribute is non-empty, "
        "typically '3,3'); (3) the page contains a visible HTML <select> element "
        "(the binding_select dropdown) whose options include MSFT, AMZN, IBM, GOOG, "
        "and AAPL. The chart container must not display a Vega-Embed error."
    )
    result = browser_verifier.verify(
        reason=reason,
        truth=truth,
        use_browser_agent=True,
        trajectory_dir="/logs/verifier/pochi/test_browser_renders_lines_dashed_rule_and_dropdown",
    )
    assert result.status == "pass", f"Browser verification failed: {result.reason}"
