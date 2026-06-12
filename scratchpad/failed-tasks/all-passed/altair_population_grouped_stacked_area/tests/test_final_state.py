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

EXPECTED_TITLE = "US Population Composition (Normalized)"
EXPECTED_BUCKETS = ["0-19", "20-39", "40-59", "60+"]


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


def _title_text(spec: dict[str, Any]) -> str:
    title = spec.get("title")
    if isinstance(title, str):
        return title
    if isinstance(title, dict):
        text = title.get("text")
        if isinstance(text, str):
            return text
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


def test_mark_is_area(vega_spec):
    assert _mark_type(vega_spec) == "area", (
        f"Expected the top-level mark to be `area`, got `{_mark_type(vega_spec)}`."
    )


def test_chart_size_and_title(vega_spec):
    assert vega_spec.get("width") == 700, (
        f"Expected top-level `width` to equal 700, got {vega_spec.get('width')!r}."
    )
    assert vega_spec.get("height") == 350, (
        f"Expected top-level `height` to equal 350, got {vega_spec.get('height')!r}."
    )
    assert _title_text(vega_spec) == EXPECTED_TITLE, (
        f"Expected top-level title to be {EXPECTED_TITLE!r}, "
        f"got {_title_text(vega_spec)!r}."
    )


def test_transform_calculate_buckets_age(vega_spec):
    transforms = _collect_transforms(vega_spec)
    calc_entries = [
        t for t in transforms
        if isinstance(t, dict) and "calculate" in t and t.get("as") == "age_group"
    ]
    assert calc_entries, (
        "Expected at least one `transform_calculate` entry with `as == 'age_group'` "
        "that buckets the granular `age` field into 4 age groups."
    )
    matched = False
    for t in calc_entries:
        expr = str(t.get("calculate", ""))
        if "age" not in expr:
            continue
        if all(bucket in expr for bucket in EXPECTED_BUCKETS):
            matched = True
            break
    assert matched, (
        "Expected the calculate expression for `age_group` to reference `age` and "
        f"contain all four bucket labels {EXPECTED_BUCKETS}."
    )


def test_transform_aggregate_sums_people_by_year_and_age_group(vega_spec):
    transforms = _collect_transforms(vega_spec)
    agg_entries = [
        t for t in transforms if isinstance(t, dict) and "aggregate" in t
    ]
    assert agg_entries, (
        "Expected at least one `transform_aggregate` entry that sums `people` "
        "grouped by `year` and `age_group`."
    )
    matched = False
    for t in agg_entries:
        aggregate = t.get("aggregate")
        groupby = t.get("groupby") or []
        if not isinstance(aggregate, list) or not isinstance(groupby, list):
            continue
        has_sum_people = any(
            isinstance(a, dict)
            and a.get("op") == "sum"
            and a.get("as") == "people"
            for a in aggregate
        )
        has_year = "year" in groupby
        has_age_group = "age_group" in groupby
        if has_sum_people and has_year and has_age_group:
            matched = True
            break
    assert matched, (
        "Expected an aggregate transform with `op == 'sum'` and `as == 'people'`, "
        "and `groupby` containing both `year` and `age_group`."
    )


def test_x_encoding_is_year_ordinal(vega_spec):
    encoding = vega_spec.get("encoding") or {}
    x = encoding.get("x") or {}
    assert x.get("field") == "year", (
        f"Expected `encoding.x.field` to be `'year'`, got {x.get('field')!r}."
    )
    assert x.get("type") == "ordinal", (
        f"Expected `encoding.x.type` to be `'ordinal'`, got {x.get('type')!r}."
    )


def test_y_encoding_sums_people_with_normalize_stack(vega_spec):
    encoding = vega_spec.get("encoding") or {}
    y = encoding.get("y") or {}
    assert y.get("aggregate") == "sum", (
        f"Expected `encoding.y.aggregate` to be `'sum'`, got {y.get('aggregate')!r}."
    )
    assert y.get("field") == "people", (
        f"Expected `encoding.y.field` to be `'people'`, got {y.get('field')!r}."
    )
    assert y.get("stack") == "normalize", (
        f"Expected `encoding.y.stack` to be `'normalize'`, got {y.get('stack')!r}."
    )


def test_color_encoding_uses_ordered_age_groups_and_tableau10(vega_spec):
    encoding = vega_spec.get("encoding") or {}
    color = encoding.get("color") or {}
    assert color.get("field") == "age_group", (
        f"Expected `encoding.color.field` to be `'age_group'`, got {color.get('field')!r}."
    )
    assert color.get("type") == "nominal", (
        f"Expected `encoding.color.type` to be `'nominal'`, got {color.get('type')!r}."
    )
    sort_value = color.get("sort")
    assert isinstance(sort_value, list), (
        f"Expected `encoding.color.sort` to be a list, got {type(sort_value).__name__}."
    )
    assert sort_value == EXPECTED_BUCKETS, (
        f"Expected `encoding.color.sort` to equal {EXPECTED_BUCKETS}, got {sort_value}."
    )
    scale = color.get("scale") or {}
    assert scale.get("scheme") == "tableau10", (
        f"Expected `encoding.color.scale.scheme` to be `'tableau10'`, "
        f"got {scale.get('scheme')!r}."
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


def test_browser_renders_normalized_stacked_area(chart_preview_server):
    reason = (
        "The Altair-generated chart.html must render a normalized stacked area chart of "
        "US population composition by age group. The y axis must span the full 0..1 "
        "(or 0..100%) range so the chart looks full-height, there must be exactly 4 "
        "stacked colored bands, and a legend must list the four age groups "
        "(`0-19`, `20-39`, `40-59`, `60+`)."
    )
    truth = (
        f"Navigate to {chart_preview_server} in a browser. "
        "Wait for the Vega-Lite chart to finish rendering. "
        "Verify that the page has no JavaScript console errors. "
        f"Verify the chart's title reads `{EXPECTED_TITLE}`. "
        "Verify that the y axis spans the full 0..1 (or 0..100%) range and the "
        "topmost band reaches the top of the plot area (i.e. the stacked area is "
        "normalized / full-height). "
        "Verify that the plot area contains exactly 4 stacked colored bands. "
        "Verify that a color legend is visible and lists exactly these four "
        "age groups in order: `0-19`, `20-39`, `40-59`, `60+`."
    )
    verifier = PochiVerifier()
    result = verifier.verify(
        reason=reason,
        truth=truth,
        use_browser_agent=True,
        trajectory_dir="/logs/verifier/pochi/test_browser_renders_normalized_stacked_area",
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
