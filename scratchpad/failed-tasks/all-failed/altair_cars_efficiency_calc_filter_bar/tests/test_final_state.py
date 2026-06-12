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


def test_top_level_mark_is_bar(vega_spec):
    mark_type = _mark_type(vega_spec)
    assert mark_type == "bar", (
        f"Expected the top-level chart `mark` to be `bar`, got `{mark_type!r}`."
    )


def test_transform_calculate_derives_efficiency(vega_spec):
    transforms = _collect_transforms(vega_spec)
    calc_transforms = [t for t in transforms if isinstance(t, dict) and "calculate" in t]
    assert calc_transforms, (
        "Expected at least one `transform_calculate` entry in the spec's `transform` "
        "list that derives the `Efficiency` field."
    )
    matched = None
    for t in calc_transforms:
        expr = str(t.get("calculate", ""))
        as_field = str(t.get("as", ""))
        if (
            "Miles_per_Gallon" in expr
            and "Weight_in_lbs" in expr
            and as_field == "Efficiency"
        ):
            matched = t
            break
    assert matched is not None, (
        "Expected a calculate transform whose expression references both "
        "`Miles_per_Gallon` and `Weight_in_lbs`, and whose `as` field equals "
        f"`Efficiency`. Got calculate transforms: {calc_transforms}."
    )


def test_transform_filter_drops_low_efficiency(vega_spec):
    transforms = _collect_transforms(vega_spec)
    filter_transforms = [t for t in transforms if isinstance(t, dict) and "filter" in t]
    assert filter_transforms, (
        "Expected at least one `transform_filter` entry in the spec's `transform` list."
    )

    def _flatten_filter(value: Any) -> str:
        # Filter can be a string expression, or a dict (field-predicate form). We
        # convert to JSON so we can search for the keywords regardless of shape.
        if isinstance(value, str):
            return value
        try:
            return json.dumps(value)
        except (TypeError, ValueError):
            return str(value)

    matched = False
    for t in filter_transforms:
        flat = _flatten_filter(t.get("filter"))
        if "Efficiency" in flat and "0.01" in flat and ">" in flat:
            matched = True
            break
    assert matched, (
        "Expected a filter transform whose expression references the `Efficiency` "
        "field with a greater-than comparison against `0.01` (e.g. "
        "`datum.Efficiency > 0.01`). Got filter transforms: "
        f"{filter_transforms}."
    )


def test_calculate_before_filter_in_transform(vega_spec):
    transforms = _collect_transforms(vega_spec)
    calc_idx = None
    filter_idx = None
    for i, t in enumerate(transforms):
        if not isinstance(t, dict):
            continue
        if calc_idx is None and "calculate" in t and str(t.get("as", "")) == "Efficiency":
            calc_idx = i
        if (
            filter_idx is None
            and "filter" in t
            and "Efficiency" in json.dumps(t.get("filter"))
        ):
            filter_idx = i
    assert calc_idx is not None, (
        "Could not find a calculate transform with `as == 'Efficiency'`."
    )
    assert filter_idx is not None, (
        "Could not find a filter transform referencing `Efficiency`."
    )
    assert calc_idx < filter_idx, (
        "Expected the `calculate` transform that derives `Efficiency` to appear "
        "before the `filter` transform that uses it. "
        f"calculate index={calc_idx}, filter index={filter_idx}."
    )


def test_x_encoding_is_ordinal_cylinders_ascending(vega_spec):
    encoding = vega_spec.get("encoding") or {}
    x = encoding.get("x")
    assert isinstance(x, dict), (
        f"Expected `encoding.x` to be an object, got {type(x).__name__}: {x!r}."
    )
    assert x.get("field") == "Cylinders", (
        f"Expected `encoding.x.field == 'Cylinders'`, got {x.get('field')!r}."
    )
    assert x.get("type") == "ordinal", (
        f"Expected `encoding.x.type == 'ordinal'`, got {x.get('type')!r}."
    )
    assert x.get("sort") == "ascending", (
        f"Expected `encoding.x.sort == 'ascending'`, got {x.get('sort')!r}."
    )


def test_y_encoding_is_mean_efficiency_with_axis_title(vega_spec):
    encoding = vega_spec.get("encoding") or {}
    y = encoding.get("y")
    assert isinstance(y, dict), (
        f"Expected `encoding.y` to be an object, got {type(y).__name__}: {y!r}."
    )
    assert y.get("aggregate") == "mean", (
        f"Expected `encoding.y.aggregate == 'mean'`, got {y.get('aggregate')!r}."
    )
    assert y.get("field") == "Efficiency", (
        f"Expected `encoding.y.field == 'Efficiency'`, got {y.get('field')!r}."
    )
    assert y.get("type") == "quantitative", (
        f"Expected `encoding.y.type == 'quantitative'`, got {y.get('type')!r}."
    )
    axis = y.get("axis") or {}
    title = axis.get("title")
    assert isinstance(title, str) and "Mean Efficiency" in title, (
        "Expected `encoding.y.axis.title` to be a string containing "
        f"'Mean Efficiency'. Got {title!r}."
    )


def test_color_encoding_is_ordinal_cylinders_category10(vega_spec):
    encoding = vega_spec.get("encoding") or {}
    color = encoding.get("color")
    assert isinstance(color, dict), (
        f"Expected `encoding.color` to be an object, got "
        f"{type(color).__name__}: {color!r}."
    )
    assert color.get("field") == "Cylinders", (
        f"Expected `encoding.color.field == 'Cylinders'`, got {color.get('field')!r}."
    )
    assert color.get("type") == "ordinal", (
        f"Expected `encoding.color.type == 'ordinal'`, got {color.get('type')!r}."
    )
    scale = color.get("scale") or {}
    assert scale.get("scheme") == "category10", (
        "Expected `encoding.color.scale.scheme == 'category10'`, got "
        f"{scale.get('scheme')!r}."
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


def test_browser_renders_cylinder_bars(chart_preview_server):
    reason = (
        "The Altair-generated chart.html must render a bar chart that summarizes the "
        "cars dataset by `Cylinders`, using a calculate+filter pipeline that derives "
        "`Efficiency = Miles_per_Gallon / Weight_in_lbs` and drops rows with "
        "`Efficiency <= 0.01`. The chart must show one bar per surviving cylinder "
        "count, colored by Vega's `category10` scheme, with a y-axis titled "
        "`Mean Efficiency (mpg/lb)` (or another string containing `Mean Efficiency`)."
    )
    truth = (
        f"Navigate to {chart_preview_server} in a browser. "
        "Wait for the Vega-Lite chart to finish rendering. "
        "Verify that the page has no JavaScript console errors. "
        "Verify that the rendered chart visibly contains exactly 5 vertical bars, "
        "one per distinct cylinder count from the cars dataset (3, 4, 5, 6, and 8 "
        "cylinders), each drawn in a different color from the `category10` palette. "
        "Verify that the x-axis is labelled `Cylinders` with the bars ordered "
        "ascending from left to right, and that the y-axis title visibly contains "
        "the substring `Mean Efficiency`."
    )
    verifier = PochiVerifier()
    result = verifier.verify(
        reason=reason,
        truth=truth,
        use_browser_agent=True,
        trajectory_dir="/logs/verifier/pochi/test_browser_renders_cylinder_bars",
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
