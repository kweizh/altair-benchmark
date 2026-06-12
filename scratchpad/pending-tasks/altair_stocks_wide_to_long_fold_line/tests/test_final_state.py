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


def _mark_type(spec: dict[str, Any]) -> str:
    mark = spec.get("mark")
    if isinstance(mark, str):
        return mark
    if isinstance(mark, dict):
        return str(mark.get("type", ""))
    return ""


def _collect_transforms(spec: dict[str, Any]) -> list[dict[str, Any]]:
    transforms: list[dict[str, Any]] = []
    if isinstance(spec.get("transform"), list):
        transforms.extend(spec["transform"])
    for layer in spec.get("layer", []) or []:
        if isinstance(layer, dict) and isinstance(layer.get("transform"), list):
            transforms.extend(layer["transform"])
    return transforms


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


def test_mark_is_line(vega_spec):
    mark_type = _mark_type(vega_spec)
    assert mark_type == "line", (
        f"Expected the spec's mark type to be 'line', got '{mark_type}'."
    )


def test_fold_transform_configured(vega_spec):
    transforms = _collect_transforms(vega_spec)
    fold_entries = [
        t for t in transforms if isinstance(t, dict) and "fold" in t
    ]
    assert fold_entries, (
        "Expected the spec to contain at least one transform entry with a `fold` key "
        "(produced by `transform_fold`)."
    )
    matched = None
    for entry in fold_entries:
        fold = entry.get("fold")
        as_field = entry.get("as")
        if (
            isinstance(fold, list)
            and list(fold) == ["AAPL", "AMZN", "GOOG"]
            and isinstance(as_field, list)
            and list(as_field) == ["company", "price"]
        ):
            matched = entry
            break
    assert matched is not None, (
        "Expected a fold transform with fold == ['AAPL', 'AMZN', 'GOOG'] and "
        f"as == ['company', 'price']. Found fold transform entries: {fold_entries}."
    )


def test_x_encoding_is_date_temporal(vega_spec):
    encoding = vega_spec.get("encoding") or {}
    x = encoding.get("x") or {}
    assert isinstance(x, dict), "Expected `encoding.x` to be an object."
    assert x.get("field") == "Date", (
        f"Expected encoding.x.field == 'Date', got {x.get('field')!r}."
    )
    assert x.get("type") == "temporal", (
        f"Expected encoding.x.type == 'temporal', got {x.get('type')!r}."
    )


def test_y_encoding_is_price_quantitative(vega_spec):
    encoding = vega_spec.get("encoding") or {}
    y = encoding.get("y") or {}
    assert isinstance(y, dict), "Expected `encoding.y` to be an object."
    assert y.get("field") == "price", (
        f"Expected encoding.y.field == 'price', got {y.get('field')!r}."
    )
    assert y.get("type") == "quantitative", (
        f"Expected encoding.y.type == 'quantitative', got {y.get('type')!r}."
    )


def test_color_encoding_is_company_nominal(vega_spec):
    encoding = vega_spec.get("encoding") or {}
    color = encoding.get("color") or {}
    assert isinstance(color, dict), "Expected `encoding.color` to be an object."
    assert color.get("field") == "company", (
        f"Expected encoding.color.field == 'company', got {color.get('field')!r}."
    )
    assert color.get("type") == "nominal", (
        f"Expected encoding.color.type == 'nominal', got {color.get('type')!r}."
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


def test_browser_renders_three_company_lines(chart_preview_server):
    reason = (
        "The Altair-generated chart.html must render a multi-line chart of monthly stock "
        "prices for three companies (AAPL, AMZN, GOOG), produced by folding a wide-form "
        "DataFrame with `transform_fold` and encoding the folded `company` field on color."
    )
    truth = (
        f"Navigate to {chart_preview_server} in a browser. "
        "Wait for the Vega-Lite chart to finish rendering. "
        "Verify that the page has no JavaScript console errors. "
        "Verify that the rendered chart contains exactly three distinct colored line paths "
        "(one line per company). "
        "Verify that the chart has a color legend listing the three series labels "
        "`AAPL`, `AMZN`, and `GOOG` (all three must be present in the legend)."
    )
    verifier = PochiVerifier()
    result = verifier.verify(
        reason=reason,
        truth=truth,
        use_browser_agent=True,
        trajectory_dir="/logs/verifier/pochi/test_browser_renders_three_company_lines",
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
