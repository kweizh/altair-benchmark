import csv
import json
import os
import re
import socket
import subprocess
from typing import Any, Iterable

import pytest
from xprocess import ProcessStarter

from pochi_verifier import PochiVerifier

PROJECT_DIR = "/home/user/myproject"
CHART_HTML = os.path.join(PROJECT_DIR, "chart.html")
BUILD_SCRIPT = os.path.join(PROJECT_DIR, "build_chart.py")
CSV_PATH = os.path.join(PROJECT_DIR, "transformed_data.csv")
PREVIEW_PORT = 8765


# ---------------------------------------------------------------------------
# Helpers for walking the embedded Vega / Vega-Lite spec.
# ---------------------------------------------------------------------------


def _extract_spec(html: str) -> dict[str, Any]:
    """Extract the embedded chart spec from an Altair-saved HTML file.

    When VegaFusion is enabled, Altair compiles the spec to Vega before saving,
    so the embedded spec may be either a Vega-Lite or a Vega spec.
    """
    patterns = [
        r"var\s+spec\s*=\s*(\{.*?\})\s*;\s*var\s+embedOpt",
        r"vegaEmbed\(\s*[\"'][^\"']+[\"']\s*,\s*(\{.*?\})\s*[,)]",
        r"<script[^>]*type=[\"']application/json[\"'][^>]*>(\{.*?\})</script>",
    ]
    for pat in patterns:
        m = re.search(pat, html, re.DOTALL)
        if m is not None:
            raw = m.group(1)
            try:
                return json.loads(raw)
            except json.JSONDecodeError:
                continue
    raise AssertionError(
        "Could not find an embedded Vega/Vega-Lite JSON spec inside chart.html. "
        "Expected an Altair-style `var spec = {...};` block, a vegaEmbed(...) "
        "call, or a `<script type=\"application/json\">` block."
    )


def _walk(node: Any) -> Iterable[Any]:
    """Yield every dict or list found anywhere in the spec tree."""
    stack: list[Any] = [node]
    while stack:
        cur = stack.pop()
        if isinstance(cur, dict):
            yield cur
            stack.extend(cur.values())
        elif isinstance(cur, list):
            yield cur
            stack.extend(cur)


def _mark_types_in_spec(spec: dict[str, Any]) -> set[str]:
    """Collect every mark type referenced anywhere in the spec (Vega or VL)."""
    marks: set[str] = set()
    for node in _walk(spec):
        if not isinstance(node, dict):
            continue
        # Vega-Lite mark shorthand
        mark = node.get("mark")
        if isinstance(mark, str):
            marks.add(mark)
        elif isinstance(mark, dict):
            t = mark.get("type")
            if isinstance(t, str):
                marks.add(t)
        # Vega-style marks live in arrays with {"type": ..., ...} entries.
        if "type" in node and isinstance(node.get("type"), str):
            # Heuristic: this is a Vega mark if it sits under a "marks" array,
            # but we cannot easily test that here; just collect candidate types.
            # We restrict to known mark types of interest later.
            marks.add(node["type"])
    return marks


def _has_rect_mark(spec: dict[str, Any]) -> bool:
    if "rect" in _mark_types_in_spec(spec):
        return True
    # Fallback: explicit search for {"type": "rect"} dicts.
    for node in _walk(spec):
        if isinstance(node, dict) and node.get("type") == "rect":
            return True
    return False


def _maxbins_values(spec: dict[str, Any]) -> list[int]:
    """Collect every numeric `maxbins` value referenced in the spec."""
    values: list[int] = []
    for node in _walk(spec):
        if not isinstance(node, dict):
            continue
        # Vega-Lite: encoding.x = {"field": "x", "bin": {"maxbins": 20}, ...}
        bin_val = node.get("bin")
        if isinstance(bin_val, dict):
            mb = bin_val.get("maxbins")
            if isinstance(mb, (int, float)):
                values.append(int(mb))
        # Vega bin transform: {"type": "bin", "maxbins": 20, ...}
        if node.get("type") == "bin":
            mb = node.get("maxbins")
            if isinstance(mb, (int, float)):
                values.append(int(mb))
        # Sometimes maxbins shows up as a direct numeric property elsewhere
        if "maxbins" in node and isinstance(node["maxbins"], (int, float)):
            values.append(int(node["maxbins"]))
    return values


def _has_mean_aggregate_on_z(spec: dict[str, Any]) -> bool:
    """Return True if the spec aggregates field `z` with op `mean`."""
    for node in _walk(spec):
        if not isinstance(node, dict):
            continue
        # Vega-Lite color encoding: {"field": "z", "aggregate": "mean", ...}
        if (
            node.get("aggregate") == "mean"
            and (node.get("field") == "z" or "z" in str(node.get("field", "")))
        ):
            return True
        # Vega aggregate transform: {"type": "aggregate", "ops": [...], "fields": [...]}
        if node.get("type") == "aggregate":
            ops = node.get("ops")
            fields = node.get("fields")
            if isinstance(ops, list) and isinstance(fields, list):
                for op, field in zip(ops, fields):
                    if op == "mean" and (field == "z" or "z" in str(field or "")):
                        return True
    return False


def _has_magma_scheme(spec: dict[str, Any]) -> bool:
    """Return True if a 'magma' color scheme is referenced anywhere."""
    for node in _walk(spec):
        if isinstance(node, dict):
            scheme = node.get("scheme")
            if isinstance(scheme, str) and scheme == "magma":
                return True
            if isinstance(scheme, dict) and scheme.get("name") == "magma":
                return True
            # Vega scales: {"range": {"scheme": "magma"}}
            rng = node.get("range")
            if isinstance(rng, dict) and rng.get("scheme") == "magma":
                return True
    return False


# ---------------------------------------------------------------------------
# Fixtures.
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def chart_spec() -> dict[str, Any]:
    assert os.path.isfile(CHART_HTML), (
        f"Expected the executor to produce {CHART_HTML} after running build_chart.py."
    )
    with open(CHART_HTML, "r", encoding="utf-8") as f:
        html = f.read()
    assert len(html) > 0, f"{CHART_HTML} is empty."
    return _extract_spec(html)


# ---------------------------------------------------------------------------
# Truth checks.
# ---------------------------------------------------------------------------


def test_build_script_exists():
    assert os.path.isfile(BUILD_SCRIPT), (
        f"Expected build script {BUILD_SCRIPT} to exist."
    )


def test_build_script_enables_vegafusion():
    with open(BUILD_SCRIPT, "r", encoding="utf-8") as f:
        source = f.read()
    pattern = re.compile(
        r"data_transformers\s*\.\s*enable\s*\(\s*['\"]vegafusion['\"]\s*\)"
    )
    assert pattern.search(source) is not None, (
        "Expected build_chart.py to call alt.data_transformers.enable('vegafusion') "
        "(or the double-quoted equivalent) so the 60,000-row dataset bypasses "
        "Altair's default MaxRowsError limit."
    )


def test_build_script_runs_without_max_rows_error():
    """Re-run the executor's script and confirm it does not raise MaxRowsError."""
    result = subprocess.run(
        ["python3", "build_chart.py"],
        capture_output=True,
        text=True,
        cwd=PROJECT_DIR,
    )
    assert result.returncode == 0, (
        f"`python3 build_chart.py` failed with exit code {result.returncode}.\n"
        f"stdout: {result.stdout}\nstderr: {result.stderr}"
    )
    combined = f"{result.stdout}\n{result.stderr}"
    assert "MaxRowsError" not in combined, (
        "build_chart.py emitted a MaxRowsError, which means VegaFusion is not "
        "actually disabling Altair's row limit. Combined output:\n" + combined
    )


def test_chart_html_exists_and_non_empty():
    assert os.path.isfile(CHART_HTML), (
        f"Expected {CHART_HTML} to be produced by `python3 build_chart.py`."
    )
    assert os.path.getsize(CHART_HTML) > 0, f"{CHART_HTML} is empty."


def test_chart_uses_rect_mark(chart_spec):
    assert _has_rect_mark(chart_spec), (
        "Expected the chart spec embedded in chart.html to use a `rect` mark "
        "(mark_rect) for the heatmap, but no rect mark was found."
    )


def test_chart_has_two_maxbins_20(chart_spec):
    values = _maxbins_values(chart_spec)
    twenty = [v for v in values if v == 20]
    assert len(twenty) >= 2, (
        "Expected the heatmap spec to bin both the X and Y channels with "
        f"maxbins=20 (so two `maxbins: 20` entries should appear). Found "
        f"maxbins values: {values}."
    )


def test_chart_color_aggregates_mean_of_z(chart_spec):
    assert _has_mean_aggregate_on_z(chart_spec), (
        "Expected the chart spec to aggregate field `z` with op `mean` for the "
        "color channel (either as a Vega-Lite color encoding "
        "`{field: 'z', aggregate: 'mean'}` or a Vega aggregate transform with "
        "ops=['mean'] and fields=['z'])."
    )


def test_chart_color_scheme_is_magma(chart_spec):
    assert _has_magma_scheme(chart_spec), (
        "Expected the color scale to use the 'magma' color scheme. None of the "
        "scale entries referenced scheme='magma'."
    )


def test_transformed_data_csv_exists_and_is_valid():
    assert os.path.isfile(CSV_PATH), (
        f"Expected {CSV_PATH} to be produced from chart.transformed_data()."
    )
    assert os.path.getsize(CSV_PATH) > 0, f"{CSV_PATH} is empty."
    with open(CSV_PATH, "r", encoding="utf-8", newline="") as f:
        reader = csv.reader(f)
        rows = list(reader)
    assert len(rows) >= 1, f"{CSV_PATH} has no rows at all."
    header = rows[0]
    data_rows = rows[1:]
    assert len(data_rows) >= 50, (
        f"Expected at least 50 aggregated bin rows in {CSV_PATH}, found "
        f"{len(data_rows)}."
    )
    # The mean-of-z column may be named 'z', 'mean_z', 'mean(z)', or similar.
    assert any("z" in (col or "").lower() for col in header), (
        f"Expected at least one column referencing `z` (the aggregated mean-of-z "
        f"column) in {CSV_PATH}. Header was: {header}."
    )


# ---------------------------------------------------------------------------
# Browser verification.
# ---------------------------------------------------------------------------


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


def test_browser_renders_heatmap(chart_preview_server):
    reason = (
        "The chart.html produced by build_chart.py must render an Altair / "
        "Vega-Lite 2D binned heatmap of a 60,000-row synthetic dataset whose "
        "color encodes the mean of `z` per (x, y) bin. The chart must use the "
        "magma color scheme and must render successfully in the browser even "
        "though the source dataset exceeds Altair's default 5,000-row limit "
        "(this is achieved by enabling the VegaFusion data transformer)."
    )
    truth = (
        f"Navigate to {chart_preview_server} in a browser. "
        "Wait for the Vega/Vega-Lite chart to finish rendering. "
        "Verify that the page has no JavaScript console errors. "
        "Verify that the rendered output contains a visible heatmap drawn as a "
        "grid of small rectangles (the binned (x, y) cells), and that there is "
        "a continuous color legend on the side of the plot whose color ramp "
        "matches the 'magma' colormap (dark purple/black at the low end, "
        "transitioning through reds and oranges to a bright yellow/cream at "
        "the high end). The chart must NOT show any 'MaxRowsError' message or "
        "an empty plot area."
    )
    verifier = PochiVerifier()
    result = verifier.verify(
        reason=reason,
        truth=truth,
        use_browser_agent=True,
        trajectory_dir="/logs/verifier/pochi/test_browser_renders_heatmap",
    )
    assert result.status == "pass", f"Browser verification failed: {result.reason}"
