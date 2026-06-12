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

EXPECTED_COLOR_MAP = {
    "sun": "#e7ba52",
    "fog": "#c7c7c7",
    "drizzle": "#aec7e8",
    "rain": "#1f77b4",
    "snow": "#9467bd",
}


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


def _mark_type(mark: Any) -> str:
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


def test_spec_is_single_bar_chart(vega_spec):
    assert "layer" not in vega_spec, (
        "Expected a single (non-layered) bar chart, but the spec contains a top-level `layer` array."
    )
    mark = vega_spec.get("mark")
    assert mark is not None, "Top-level Vega-Lite spec must define a `mark`."
    assert _mark_type(mark) == "bar", (
        f"Expected top-level mark type `bar`, found `{_mark_type(mark)}`."
    )


def test_y_encoding_is_nominal_weather(vega_spec):
    encoding = vega_spec.get("encoding") or {}
    y = encoding.get("y")
    assert isinstance(y, dict), (
        f"Expected `encoding.y` to be a dict, got: {y!r}."
    )
    assert y.get("field") == "weather", (
        f"Expected `encoding.y.field` to be `weather`, got: {y.get('field')!r}."
    )
    assert y.get("type") == "nominal", (
        f"Expected `encoding.y.type` to be `nominal`, got: {y.get('type')!r}."
    )


def test_x_encoding_is_count_aggregate_with_no_field(vega_spec):
    encoding = vega_spec.get("encoding") or {}
    x = encoding.get("x")
    assert isinstance(x, dict), (
        f"Expected `encoding.x` to be a dict, got: {x!r}."
    )
    assert x.get("aggregate") == "count", (
        f"Expected `encoding.x.aggregate` to be `count`, got: {x.get('aggregate')!r}."
    )
    assert "field" not in x, (
        "Expected the `count` aggregate on `encoding.x` to count all rows "
        "(no `field` key), but a `field` was set: "
        f"{x.get('field')!r}."
    )


def test_color_encoding_uses_custom_domain_and_range(vega_spec):
    encoding = vega_spec.get("encoding") or {}
    color = encoding.get("color")
    assert isinstance(color, dict), (
        f"Expected `encoding.color` to be a dict, got: {color!r}."
    )
    assert color.get("field") == "weather", (
        f"Expected `encoding.color.field` to be `weather`, got: {color.get('field')!r}."
    )

    scale = color.get("scale")
    assert isinstance(scale, dict), (
        f"Expected `encoding.color.scale` to be a dict with a custom `domain`/`range`, got: {scale!r}."
    )

    domain = scale.get("domain")
    range_ = scale.get("range")
    assert isinstance(domain, list), (
        f"Expected `encoding.color.scale.domain` to be a list, got: {domain!r}."
    )
    assert isinstance(range_, list), (
        f"Expected `encoding.color.scale.range` to be a list, got: {range_!r}."
    )

    expected_domain = set(EXPECTED_COLOR_MAP.keys())
    expected_range = set(EXPECTED_COLOR_MAP.values())

    assert set(domain) == expected_domain, (
        f"Expected `scale.domain` to contain exactly {sorted(expected_domain)}, "
        f"got: {sorted(domain)}."
    )

    # Normalize hex codes to lowercase for comparison.
    normalized_range = [
        str(c).lower() if isinstance(c, str) else c for c in range_
    ]
    expected_range_normalized = {c.lower() for c in expected_range}
    assert set(normalized_range) == expected_range_normalized, (
        f"Expected `scale.range` to contain exactly {sorted(expected_range_normalized)}, "
        f"got: {sorted(normalized_range)}."
    )

    assert len(domain) == len(range_) == 5, (
        f"Expected `scale.domain` and `scale.range` to each have 5 entries, "
        f"got len(domain)={len(domain)}, len(range)={len(range_)}."
    )

    # Build the index-aligned category -> color mapping.
    actual_map = {
        str(cat): str(col).lower()
        for cat, col in zip(domain, normalized_range)
    }
    expected_map_normalized = {
        cat: col.lower() for cat, col in EXPECTED_COLOR_MAP.items()
    }
    assert actual_map == expected_map_normalized, (
        f"Expected the index-aligned domain->range mapping to equal "
        f"{expected_map_normalized}, got: {actual_map}."
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


def test_browser_renders_five_colored_bars(chart_preview_server):
    reason = (
        "The Altair-generated chart.html must render a horizontal bar chart of Seattle weather "
        "category counts where each bar is colored by the `weather` field using a custom categorical "
        "color scale (sun=#e7ba52, fog=#c7c7c7, drizzle=#aec7e8, rain=#1f77b4, snow=#9467bd). "
        "The rendered chart must show exactly 5 horizontal bars (one per category) and a visible legend."
    )
    truth = (
        f"Navigate to {chart_preview_server} in a browser. "
        "Wait for the Vega-Lite chart to finish rendering. "
        "Verify the page has no JavaScript console errors. "
        "Verify that the rendered chart shows exactly 5 horizontal bars (one per weather category: "
        "sun, fog, drizzle, rain, snow), each running horizontally from the y axis to a length "
        "proportional to the count of days in that category. "
        "Verify that the bars use the following exact custom colors (any small rounding of color "
        "values is acceptable): sun -> #e7ba52, fog -> #c7c7c7, drizzle -> #aec7e8, rain -> #1f77b4, "
        "snow -> #9467bd. "
        "Verify that a color legend tied to the `weather` field is visible and that the legend swatch "
        "for each category matches the corresponding bar color."
    )
    verifier = PochiVerifier()
    result = verifier.verify(
        reason=reason,
        truth=truth,
        use_browser_agent=True,
        trajectory_dir="/logs/verifier/pochi/test_browser_renders_five_colored_bars",
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
