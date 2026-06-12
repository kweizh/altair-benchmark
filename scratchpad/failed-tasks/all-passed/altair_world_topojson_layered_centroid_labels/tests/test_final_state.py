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

EXPECTED_CITIES = {"Tokyo", "London", "New York", "Sao Paulo", "Sydney"}


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


def _mark_props(layer: dict[str, Any]) -> dict[str, Any]:
    """Normalize a layer's mark to a dict-like view with at least a `type` field."""
    mark = layer.get("mark")
    if isinstance(mark, str):
        return {"type": mark}
    if isinstance(mark, dict):
        return mark
    return {}


def _collect_inline_values(node: Any, out: list[dict[str, Any]]) -> None:
    """Recursively collect inline data `values` arrays from anywhere in the spec."""
    if isinstance(node, dict):
        data = node.get("data")
        if isinstance(data, dict):
            values = data.get("values")
            if isinstance(values, list):
                out.extend([v for v in values if isinstance(v, dict)])
        # Some Altair outputs put values under a top-level `datasets` mapping.
        datasets = node.get("datasets")
        if isinstance(datasets, dict):
            for v in datasets.values():
                if isinstance(v, list):
                    out.extend([d for d in v if isinstance(d, dict)])
        for v in node.values():
            _collect_inline_values(v, out)
    elif isinstance(node, list):
        for item in node:
            _collect_inline_values(item, out)


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


def test_spec_is_layered_with_at_least_three_layers(vega_spec):
    layers = vega_spec.get("layer")
    assert isinstance(layers, list), (
        "Top-level Vega-Lite spec must contain a `layer` array (this is a layered chart)."
    )
    assert len(layers) >= 3, (
        f"Expected at least 3 layers in the layered chart, found {len(layers)}."
    )


def test_layer1_country_geoshape(vega_spec):
    layer = vega_spec["layer"][0]
    mark = _mark_props(layer)
    assert mark.get("type") == "geoshape", (
        f"Expected layer[0].mark.type == 'geoshape', got {mark.get('type')!r}."
    )
    assert mark.get("fill") == "#e8e8e8", (
        f"Expected layer[0].mark.fill == '#e8e8e8', got {mark.get('fill')!r}."
    )
    assert mark.get("stroke") == "white", (
        f"Expected layer[0].mark.stroke == 'white', got {mark.get('stroke')!r}."
    )


def test_layer1_uses_world_110m_topojson_countries(vega_spec):
    layer = vega_spec["layer"][0]
    data = layer.get("data")
    assert isinstance(data, dict), (
        "Expected layer[0].data to be a data definition object referencing the world TopoJSON."
    )
    url = str(data.get("url", ""))
    assert url.endswith("world-110m.json"), (
        f"Expected layer[0].data.url to end with 'world-110m.json', got {url!r}."
    )
    fmt = data.get("format") or {}
    assert isinstance(fmt, dict), (
        "Expected layer[0].data.format to be defined for a topojson feature."
    )
    assert fmt.get("type") == "topojson", (
        f"Expected layer[0].data.format.type == 'topojson', got {fmt.get('type')!r}."
    )
    assert fmt.get("feature") == "countries", (
        f"Expected layer[0].data.format.feature == 'countries', got {fmt.get('feature')!r}."
    )


def test_layer2_red_city_circles(vega_spec):
    layer = vega_spec["layer"][1]
    mark = _mark_props(layer)
    assert mark.get("type") == "circle", (
        f"Expected layer[1].mark.type == 'circle', got {mark.get('type')!r}."
    )
    assert mark.get("color") == "red", (
        f"Expected layer[1].mark.color == 'red', got {mark.get('color')!r}."
    )
    assert mark.get("size") == 80, (
        f"Expected layer[1].mark.size == 80, got {mark.get('size')!r}."
    )
    encoding = layer.get("encoding") or {}
    lon = encoding.get("longitude") or {}
    lat = encoding.get("latitude") or {}
    assert lon.get("field") == "lon", (
        f"Expected layer[1].encoding.longitude.field == 'lon', got {lon.get('field')!r}."
    )
    assert lat.get("field") == "lat", (
        f"Expected layer[1].encoding.latitude.field == 'lat', got {lat.get('field')!r}."
    )


def test_layer3_city_text_labels(vega_spec):
    layer = vega_spec["layer"][2]
    mark = _mark_props(layer)
    assert mark.get("type") == "text", (
        f"Expected layer[2].mark.type == 'text', got {mark.get('type')!r}."
    )
    assert mark.get("dy") == -12, (
        f"Expected layer[2].mark.dy == -12, got {mark.get('dy')!r}."
    )
    encoding = layer.get("encoding") or {}
    text = encoding.get("text") or {}
    lon = encoding.get("longitude") or {}
    lat = encoding.get("latitude") or {}
    assert text.get("field") == "city", (
        f"Expected layer[2].encoding.text.field == 'city', got {text.get('field')!r}."
    )
    assert lon.get("field") == "lon", (
        f"Expected layer[2].encoding.longitude.field == 'lon', got {lon.get('field')!r}."
    )
    assert lat.get("field") == "lat", (
        f"Expected layer[2].encoding.latitude.field == 'lat', got {lat.get('field')!r}."
    )


def test_top_level_projection_size(vega_spec):
    projection = vega_spec.get("projection") or {}
    assert projection.get("type") == "naturalEarth1", (
        f"Expected top-level projection.type == 'naturalEarth1', got {projection.get('type')!r}."
    )
    assert vega_spec.get("width") == 800, (
        f"Expected top-level width == 800, got {vega_spec.get('width')!r}."
    )
    assert vega_spec.get("height") == 500, (
        f"Expected top-level height == 500, got {vega_spec.get('height')!r}."
    )


def test_inline_city_data_contains_expected_cities(vega_spec):
    inline_values: list[dict[str, Any]] = []
    _collect_inline_values(vega_spec, inline_values)
    city_records = [v for v in inline_values if "city" in v and "lat" in v and "lon" in v]
    assert city_records, (
        "Expected inline data with `city`, `lat`, and `lon` fields to be embedded in the spec."
    )
    cities = {str(v.get("city")) for v in city_records}
    missing = EXPECTED_CITIES - cities
    assert not missing, (
        f"Expected the cities DataFrame to include {sorted(EXPECTED_CITIES)}, "
        f"missing {sorted(missing)}; found {sorted(cities)}."
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


def test_browser_renders_world_map_with_city_labels(chart_preview_server):
    reason = (
        "The Altair-generated chart.html must render a layered world map using the world-110m TopoJSON "
        "with a naturalEarth1 projection. It must visibly show: (1) world country outlines as light-grey "
        "polygons with white borders, (2) exactly 5 red circular markers placed at the approximate "
        "geographic locations of Tokyo, London, New York, Sao Paulo, and Sydney, and (3) 5 text labels "
        "showing each city's name placed just above its red marker."
    )
    truth = (
        f"Navigate to {chart_preview_server} in a browser. "
        "Wait for the Vega-Lite chart to finish rendering. "
        "Verify that the page has no JavaScript console errors. "
        "Verify the rendered chart contains visible world country outlines (light grey fills with white borders). "
        "Verify that exactly 5 red circular markers are drawn on top of the map, each placed over the continent "
        "that contains its city (Tokyo over east Asia, London over western Europe, New York over the eastern US, "
        "Sao Paulo over eastern South America, and Sydney over eastern Australia). "
        "Verify that 5 text labels are visible, each rendering one of the city names "
        "(Tokyo, London, New York, Sao Paulo, Sydney) just above its corresponding red marker."
    )
    verifier = PochiVerifier()
    result = verifier.verify(
        reason=reason,
        truth=truth,
        use_browser_agent=True,
        trajectory_dir="/logs/verifier/pochi/test_browser_renders_world_map_with_city_labels",
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
