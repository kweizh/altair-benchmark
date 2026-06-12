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


def _mark_type(spec_or_layer: dict[str, Any]) -> str:
    mark = spec_or_layer.get("mark")
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


def test_mark_is_geoshape(vega_spec):
    mark_type = _mark_type(vega_spec)
    assert mark_type == "geoshape", (
        f"Expected top-level `mark` to be `geoshape`, got `{mark_type}`."
    )


def test_data_is_us_10m_states_topo_feature(vega_spec):
    data = vega_spec.get("data") or {}
    fmt = data.get("format") or {}
    assert fmt.get("feature") == "states", (
        "Expected `data.format.feature` to be `\"states\"` (from "
        "`alt.topo_feature(data.us_10m.url, 'states')`). "
        f"Got format={fmt!r}."
    )
    url = str(data.get("url", ""))
    assert url.endswith("us-10m.json"), (
        f"Expected `data.url` to end with `us-10m.json`, got `{url}`."
    )


def test_transform_lookup_for_engineers(vega_spec):
    transforms = _collect_transforms(vega_spec)
    lookup_entries = [t for t in transforms if isinstance(t, dict) and "lookup" in t]
    assert lookup_entries, (
        "Expected at least one `transform_lookup` entry attaching the "
        "engineers data to the state geometries."
    )
    matched = False
    for t in lookup_entries:
        if t.get("lookup") != "id":
            continue
        from_ = t.get("from") or {}
        if from_.get("key") != "id":
            continue
        fields = from_.get("fields") or []
        if isinstance(fields, list) and "engineers" in fields:
            matched = True
            break
    assert matched, (
        "Expected a lookup transform where `lookup == 'id'`, "
        "`from.key == 'id'`, and `from.fields` contains `'engineers'`."
    )


def test_color_engineers_on_blues_scheme(vega_spec):
    encoding = vega_spec.get("encoding") or {}
    color = encoding.get("color") or {}
    assert color.get("field") == "engineers", (
        f"Expected `encoding.color.field == 'engineers'`, got `{color.get('field')!r}`."
    )
    scale = color.get("scale") or {}
    assert scale.get("scheme") == "blues", (
        "Expected `encoding.color.scale.scheme == 'blues'`, "
        f"got `{scale.get('scheme')!r}`."
    )


def test_tooltip_includes_state_and_engineers(vega_spec):
    encoding = vega_spec.get("encoding") or {}
    tooltip = encoding.get("tooltip")
    assert isinstance(tooltip, list), (
        f"Expected `encoding.tooltip` to be a list of field references, got {type(tooltip).__name__}."
    )
    fields: list[str] = []
    for entry in tooltip:
        if isinstance(entry, dict):
            f = entry.get("field")
            if isinstance(f, str):
                fields.append(f)
        elif isinstance(entry, str):
            fields.append(entry)
    assert "state" in fields, (
        f"Expected the tooltip to include the `state` field, got {fields}."
    )
    assert "engineers" in fields, (
        f"Expected the tooltip to include the `engineers` field, got {fields}."
    )


def test_projection_and_dimensions(vega_spec):
    projection = vega_spec.get("projection") or {}
    assert projection.get("type") == "albersUsa", (
        f"Expected `projection.type == 'albersUsa'`, got `{projection.get('type')!r}`."
    )
    assert vega_spec.get("width") == 700, (
        f"Expected `width == 700`, got `{vega_spec.get('width')!r}`."
    )
    assert vega_spec.get("height") == 400, (
        f"Expected `height == 400`, got `{vega_spec.get('height')!r}`."
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


def test_browser_renders_us_states_choropleth(chart_preview_server):
    reason = (
        "The Altair-generated chart.html must render a US state-level choropleth using the "
        "albersUsa projection, with each state colored on a blue gradient by the number of "
        "engineers, a visible color legend, and a working hover tooltip showing the state name "
        "and engineers count."
    )
    truth = (
        f"Navigate to {chart_preview_server} in a browser. "
        "Wait for the Vega-Lite chart to finish rendering. "
        "Verify that the page has no JavaScript console errors and that the rendered chart shows "
        "the contiguous United States with Alaska and Hawaii rendered as the standard insets of "
        "the albersUsa projection. The 50 state shapes must be filled with a blue color gradient "
        "(darker blue for higher engineer counts), and a color legend keyed to the `engineers` "
        "field must be visible. "
        "Then hover the pointer over any state and verify that a tooltip appears containing both "
        "the state name and the engineers count for that state, with no JavaScript errors."
    )
    verifier = PochiVerifier()
    result = verifier.verify(
        reason=reason,
        truth=truth,
        use_browser_agent=True,
        trajectory_dir="/logs/verifier/pochi/test_browser_renders_us_states_choropleth",
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
