import json
import os
import re
import socket

import pytest
from pochi_verifier import PochiVerifier
from xprocess import ProcessStarter

PROJECT_DIR = "/home/user/myproject"
CHART_HTML = os.path.join(PROJECT_DIR, "chart.html")
LOG_FILE = os.path.join(PROJECT_DIR, "output.log")
HTTP_PORT = 8765


def _read(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def _extract_vega_lite_spec(html_text: str) -> dict:
    """Find the Vega-Lite JSON spec embedded inside the Altair HTML output."""
    marker = '"$schema"'
    start = html_text.find(marker)
    while start != -1:
        brace = html_text.rfind("{", 0, start)
        if brace < 0:
            start = html_text.find(marker, start + 1)
            continue
        depth = 0
        in_str = False
        esc = False
        i = brace
        while i < len(html_text):
            ch = html_text[i]
            if in_str:
                if esc:
                    esc = False
                elif ch == "\\":
                    esc = True
                elif ch == '"':
                    in_str = False
            else:
                if ch == '"':
                    in_str = True
                elif ch == "{":
                    depth += 1
                elif ch == "}":
                    depth -= 1
                    if depth == 0:
                        candidate = html_text[brace : i + 1]
                        try:
                            obj = json.loads(candidate)
                            if (
                                isinstance(obj, dict)
                                and "vega-lite" in str(obj.get("$schema", ""))
                            ):
                                return obj
                        except json.JSONDecodeError:
                            pass
                        break
            i += 1
        start = html_text.find(marker, start + 1)
    raise AssertionError("Could not extract a Vega-Lite spec from chart.html")


def _mark_type(mark) -> str | None:
    if isinstance(mark, str):
        return mark
    if isinstance(mark, dict):
        return mark.get("type")
    return None


def _iter_layers(spec: dict):
    """Yield all leaf layer specs, recursing into nested 'layer' arrays."""
    stack = list(spec.get("layer", []))
    while stack:
        layer = stack.pop()
        yield layer
        if isinstance(layer, dict) and isinstance(layer.get("layer"), list):
            stack.extend(layer["layer"])


def _find_aggregate_op(layer: dict, field: str, op: str) -> bool:
    enc_y = (layer.get("encoding") or {}).get("y") or {}
    if (
        isinstance(enc_y, dict)
        and enc_y.get("aggregate") == op
        and enc_y.get("field") == field
    ):
        return True
    for t in layer.get("transform", []) or []:
        if not isinstance(t, dict):
            continue
        for agg in t.get("aggregate", []) or []:
            if (
                isinstance(agg, dict)
                and agg.get("op") == op
                and agg.get("field") == field
            ):
                return True
    return False


def _normalize_color(value) -> str | None:
    if isinstance(value, str):
        return value.lower()
    return None


@pytest.fixture(scope="module")
def spec() -> dict:
    assert os.path.isfile(CHART_HTML), f"Chart file {CHART_HTML} must exist."
    return _extract_vega_lite_spec(_read(CHART_HTML))


@pytest.fixture(scope="session")
def browser_verifier():
    yield PochiVerifier()


@pytest.fixture(scope="session")
def start_static_server(xprocess):
    class Starter(ProcessStarter):
        name = "altair_static_server"
        args = ["python3", "-m", "http.server", str(HTTP_PORT)]
        env = os.environ.copy()
        popen_kwargs = {"cwd": PROJECT_DIR, "text": True}
        timeout = 60
        terminate_on_interrupt = True

        def startup_check(self):
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                return s.connect_ex(("localhost", HTTP_PORT)) == 0

    xprocess.ensure(Starter.name, Starter)
    yield
    info = xprocess.getinfo(Starter.name)
    info.terminate()


def test_chart_html_exists():
    assert os.path.isfile(CHART_HTML), f"Chart file {CHART_HTML} must exist."
    assert os.path.getsize(CHART_HTML) > 0, "Chart file must not be empty."


def test_log_file_records_chart_path():
    assert os.path.isfile(LOG_FILE), f"Log file {LOG_FILE} must exist."
    log_text = _read(LOG_FILE)
    assert re.search(
        r"Chart written:\s*/home/user/myproject/chart\.html", log_text
    ), (
        "Log file must contain a line matching "
        "'Chart written: /home/user/myproject/chart.html'. "
        f"Got log contents:\n{log_text}"
    )


def test_spec_is_layered(spec: dict):
    assert "layer" in spec, "Top-level Vega-Lite spec must be a layered spec."
    assert isinstance(spec["layer"], list), "'layer' must be a list."
    assert len(spec["layer"]) >= 4, (
        f"Expected at least 4 layers, got {len(spec['layer'])}."
    )


def test_errorband_layer(spec: dict):
    matches: list[dict] = []
    for layer in _iter_layers(spec):
        if not isinstance(layer, dict):
            continue
        mark = layer.get("mark")
        if _mark_type(mark) != "errorband":
            continue
        assert isinstance(mark, dict), (
            "errorband layer must use an object mark to declare extent/interpolate."
        )
        assert mark.get("extent") == "iqr", (
            f"errorband.extent must be 'iqr', got {mark.get('extent')!r}."
        )
        assert mark.get("interpolate") == "monotone", (
            f"errorband.interpolate must be 'monotone', got {mark.get('interpolate')!r}."
        )
        matches.append(layer)
    assert matches, (
        "At least one layer must use mark_errorband with extent='iqr' and "
        "interpolate='monotone'."
    )


def test_line_layer_median(spec: dict):
    matches: list[dict] = []
    for layer in _iter_layers(spec):
        if not isinstance(layer, dict):
            continue
        if _mark_type(layer.get("mark")) != "line":
            continue
        if _find_aggregate_op(layer, "net_generation", "median"):
            matches.append(layer)
    assert matches, (
        "Expected a line layer whose y encodes median(net_generation) either via "
        "an aggregate encoding or via a transform_aggregate producing the median."
    )


def test_rule_layer_at_zero(spec: dict):
    matches: list[dict] = []
    for layer in _iter_layers(spec):
        if not isinstance(layer, dict):
            continue
        mark = layer.get("mark")
        if _mark_type(mark) != "rule":
            continue
        stroke_dash = mark.get("strokeDash") if isinstance(mark, dict) else None
        assert stroke_dash == [4, 4], (
            f"rule.strokeDash must be [4, 4]. Got {stroke_dash!r}."
        )

        encoding = layer.get("encoding") or {}
        y_enc = encoding.get("y") or {}
        if isinstance(y_enc, dict):
            y_value = y_enc.get("datum", y_enc.get("value"))
        else:
            y_value = None
        assert y_value == 0, (
            f"rule layer must encode y at 0 via datum or value. Got y={y_enc!r}."
        )

        # Resolve color: encoded color/value takes precedence, then mark color/stroke
        color = None
        enc_color = encoding.get("color") or {}
        if isinstance(enc_color, dict) and "value" in enc_color:
            color = enc_color["value"]
        if color is None and isinstance(mark, dict):
            color = mark.get("color") or mark.get("stroke")
        assert _normalize_color(color) == "red", (
            f"rule color must be 'red'. Got {color!r}."
        )
        matches.append(layer)
    assert matches, (
        "Expected a mark_rule layer with strokeDash=[4,4], red color, and y=0."
    )


def test_text_layer_with_window_rank(spec: dict):
    matches: list[dict] = []
    for layer in _iter_layers(spec):
        if not isinstance(layer, dict):
            continue
        if _mark_type(layer.get("mark")) != "text":
            continue
        transforms = layer.get("transform") or []
        has_rank = False
        has_rank_filter = False
        for t in transforms:
            if not isinstance(t, dict):
                continue
            if "window" in t:
                for w in t.get("window", []) or []:
                    if isinstance(w, dict) and w.get("op") == "rank":
                        has_rank = True
            if "filter" in t:
                flt = t.get("filter")
                if isinstance(flt, str) and re.search(r"==\s*1", flt):
                    has_rank_filter = True
                elif isinstance(flt, dict):
                    if flt.get("equal") == 1:
                        has_rank_filter = True
        if has_rank and has_rank_filter:
            matches.append(layer)
    assert matches, (
        "Expected a mark_text layer with a transform_window using the rank "
        "operation and a filter keeping only the row where the rank equals 1."
    )


def test_x_axis_is_temporal_with_time_scale(spec: dict):
    temporal = False
    has_time_scale = False
    for layer in [spec, *list(_iter_layers(spec))]:
        if not isinstance(layer, dict):
            continue
        x = (layer.get("encoding") or {}).get("x")
        if isinstance(x, dict):
            if x.get("type") == "temporal":
                temporal = True
            scale = x.get("scale")
            if isinstance(scale, dict) and scale.get("type") == "time":
                has_time_scale = True
    assert temporal, "Some x encoding in the spec must declare type='temporal'."
    assert has_time_scale, "Some x encoding in the spec must declare scale.type='time'."


def test_title_with_subtitle(spec: dict):
    title = spec.get("title")
    assert isinstance(title, dict), (
        f"Top-level title must be an object with both text and subtitle. Got: {title!r}"
    )
    assert title.get("text"), "Chart title must have non-empty 'text'."
    assert title.get("subtitle"), "Chart title must have non-empty 'subtitle'."


def test_browser_renders_anomaly_band(start_static_server, browser_verifier):
    reason = (
        "The chart.html file must render an Altair layered visualization of Iowa "
        "electricity net generation per year, combining an IQR error band, a "
        "median line, a dashed red horizontal rule at y=0, and a text annotation "
        "highlighting the year with the largest median net generation."
    )
    truth = (
        f"Navigate to http://localhost:{HTTP_PORT}/chart.html. "
        "Wait for the chart to render. "
        "Verify that the rendered chart contains all four of the following visual elements: "
        "(1) a filled error-band area spanning a range of values across the years; "
        "(2) a single connected line representing the median across the years drawn on top of the error band; "
        "(3) a dashed horizontal red line near the y=0 baseline; "
        "(4) a text label positioned near one specific year that shows both the year and a numeric median value. "
        "Also verify that the chart has a visible title and a smaller subtitle below it."
    )
    result = browser_verifier.verify(
        reason=reason,
        truth=truth,
        use_browser_agent=True,
        trajectory_dir="/logs/verifier/pochi/test_browser_renders_anomaly_band",
    )
    assert result.status == "pass", f"Browser verification failed: {result.reason}"
