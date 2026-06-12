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


def _mark_type(layer: dict[str, Any]) -> str:
    mark = layer.get("mark")
    if isinstance(mark, str):
        return mark
    if isinstance(mark, dict):
        return str(mark.get("type", ""))
    return ""


def _mark_obj(layer: dict[str, Any]) -> dict[str, Any]:
    mark = layer.get("mark")
    if isinstance(mark, dict):
        return mark
    return {}


def _collect_transforms(spec: dict[str, Any]) -> list[dict[str, Any]]:
    transforms: list[dict[str, Any]] = []
    if isinstance(spec.get("transform"), list):
        transforms.extend(spec["transform"])
    for layer in spec.get("layer", []) or []:
        if isinstance(layer, dict) and isinstance(layer.get("transform"), list):
            transforms.extend(layer["transform"])
    return transforms


def _is_red(color: Any) -> bool:
    if not isinstance(color, str):
        return False
    c = color.strip().lower()
    return c in {"red", "#ff0000", "#f00"}


def _datum_value(encoding_channel: Any) -> Any:
    """Return the `datum` value for an encoding channel definition, or None."""
    if not isinstance(encoding_channel, dict):
        return None
    return encoding_channel.get("datum")


def _is_oct_2008(datum: Any) -> bool:
    """Match a DateTime-like value referencing October 2008."""
    if not isinstance(datum, dict):
        return False
    year = datum.get("year")
    month = datum.get("month")
    if year != 2008:
        return False
    if isinstance(month, int):
        return month == 10
    if isinstance(month, str):
        m = month.strip().lower()
        return m in {"october", "oct"}
    return False


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


def test_spec_is_layered_with_at_least_four_layers(vega_spec):
    layers = vega_spec.get("layer")
    assert isinstance(layers, list), (
        "Top-level Vega-Lite spec must contain a `layer` array (this is a layered chart)."
    )
    assert len(layers) >= 4, (
        f"Expected at least 4 layers in the layered chart, found {len(layers)}."
    )


def test_required_mark_types_present(vega_spec):
    layers = vega_spec.get("layer", []) or []
    mark_types = [
        _mark_type(layer) for layer in layers if isinstance(layer, dict)
    ]
    assert mark_types.count("line") >= 1, (
        f"Expected at least one `line` layer, found mark types: {mark_types}."
    )
    assert mark_types.count("rule") >= 2, (
        f"Expected at least two `rule` layers, found mark types: {mark_types}."
    )
    assert mark_types.count("text") >= 1, (
        f"Expected at least one `text` layer, found mark types: {mark_types}."
    )


def test_symbol_goog_filter_transform(vega_spec):
    transforms = _collect_transforms(vega_spec)
    filter_transforms = [
        t for t in transforms if isinstance(t, dict) and "filter" in t
    ]
    assert filter_transforms, (
        "Expected at least one `transform_filter` entry to restrict the data to GOOG."
    )
    matched = False
    for t in filter_transforms:
        flt = t.get("filter")
        if isinstance(flt, str):
            if "symbol" in flt and "GOOG" in flt:
                matched = True
                break
        elif isinstance(flt, dict):
            field = str(flt.get("field", ""))
            equal = flt.get("equal")
            if field == "symbol" and equal == "GOOG":
                matched = True
                break
            # Some filter forms use `oneOf` or nested expressions; check generically.
            blob = json.dumps(flt)
            if "symbol" in blob and "GOOG" in blob:
                matched = True
                break
    assert matched, (
        "Expected a filter transform whose expression references both "
        "`symbol` and the literal `\"GOOG\"`."
    )


def test_red_dashed_threshold_rule_at_y_300(vega_spec):
    found = False
    for layer in vega_spec.get("layer", []) or []:
        if not isinstance(layer, dict):
            continue
        if _mark_type(layer) != "rule":
            continue
        encoding = layer.get("encoding") or {}
        y_datum = _datum_value(encoding.get("y"))
        if y_datum != 300:
            continue
        mark = _mark_obj(layer)
        stroke_dash = mark.get("strokeDash")
        if stroke_dash != [4, 4]:
            continue
        # Color may live on the mark definition or the encoding (as a value).
        color_ok = False
        if _is_red(mark.get("color")):
            color_ok = True
        else:
            color_enc = encoding.get("color")
            if isinstance(color_enc, dict):
                if _is_red(color_enc.get("value")) or _is_red(color_enc.get("datum")):
                    color_ok = True
        if not color_ok:
            continue
        found = True
        break
    assert found, (
        "Expected one `rule` layer with `encoding.y.datum == 300`, "
        "`mark.strokeDash == [4, 4]`, and a red color."
    )


def test_vertical_crisis_rule_at_october_2008(vega_spec):
    found = False
    for layer in vega_spec.get("layer", []) or []:
        if not isinstance(layer, dict):
            continue
        if _mark_type(layer) != "rule":
            continue
        encoding = layer.get("encoding") or {}
        x_datum = _datum_value(encoding.get("x"))
        if _is_oct_2008(x_datum):
            found = True
            break
    assert found, (
        "Expected a `rule` layer whose `encoding.x.datum` is a DateTime with "
        "`year == 2008` and `month == 10` (or `\"October\"`/`\"Oct\"`)."
    )


def test_crisis_text_annotation(vega_spec):
    found = False
    for layer in vega_spec.get("layer", []) or []:
        if not isinstance(layer, dict):
            continue
        if _mark_type(layer) != "text":
            continue
        encoding = layer.get("encoding") or {}
        text_enc = encoding.get("text")
        if isinstance(text_enc, dict):
            if text_enc.get("value") == "Crisis" or text_enc.get("datum") == "Crisis":
                found = True
                break
        # Some Altair builds inline the text via the mark definition.
        mark = _mark_obj(layer)
        if mark.get("text") == "Crisis":
            found = True
            break
    assert found, (
        "Expected a `text` layer whose `encoding.text` resolves to the literal "
        "value `\"Crisis\"` (via `value`, `datum`, or `mark.text`)."
    )


def test_spec_width_and_height(vega_spec):
    assert vega_spec.get("width") == 600, (
        f"Expected top-level `width == 600`, got {vega_spec.get('width')!r}."
    )
    assert vega_spec.get("height") == 300, (
        f"Expected top-level `height == 300`, got {vega_spec.get('height')!r}."
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


def test_browser_renders_chart_with_annotations(chart_preview_server):
    reason = (
        "The Altair-generated chart.html must render a layered GOOG stock chart that visibly "
        "combines (1) a single line of GOOG price over date, (2) a horizontal red dashed rule "
        "near the y=300 level, (3) a vertical rule near October 2008, and (4) a visible text "
        "label reading \"Crisis\" placed near that vertical rule."
    )
    truth = (
        f"Navigate to {chart_preview_server} in a browser. "
        "Wait for the Vega-Lite chart to finish rendering. "
        "Verify that the page has no JavaScript console errors and that the rendered chart "
        "contains all of the following visible marks: a single time-series line for GOOG "
        "(no other symbols rendered), a red dashed horizontal rule near the y=300 gridline, "
        "a vertical rule near the date October 2008 on the x-axis, and a text label that "
        "reads exactly `Crisis` near the vertical rule."
    )
    verifier = PochiVerifier()
    result = verifier.verify(
        reason=reason,
        truth=truth,
        use_browser_agent=True,
        trajectory_dir="/logs/verifier/pochi/test_browser_renders_chart_with_annotations",
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
