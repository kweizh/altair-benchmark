import json
import os
import re
import socket
from typing import Any

import pytest
from xprocess import ProcessStarter

from pochi_verifier import PochiVerifier


PROJECT_DIR = "/home/user/altair_choropleth_app"
CHART_HTML = os.path.join(PROJECT_DIR, "chart.html")
SERVE_PORT = 8765
SERVE_URL = f"http://localhost:{SERVE_PORT}/chart.html"

METRIC_OPTIONS = ["population", "engineers", "hurricanes"]
POPULATION_DATASET_HINT = "population_engineers_hurricanes"


# ---------------------------------------------------------------------------
# Helpers to extract the embedded Vega-Lite spec from the Altair-produced HTML
# ---------------------------------------------------------------------------


def _read_html() -> str:
    assert os.path.isfile(CHART_HTML), (
        f"Expected the build script to produce {CHART_HTML}, but the file is missing."
    )
    size = os.path.getsize(CHART_HTML)
    assert size > 0, f"Expected {CHART_HTML} to be a non-empty HTML file, got size={size}."
    with open(CHART_HTML, "r", encoding="utf-8") as f:
        return f.read()


def _balanced_json_object(text: str, start: int) -> str:
    """Return the substring starting at `start` (which must be `{`) up to its
    matching closing brace, respecting string literals and escape sequences."""
    assert text[start] == "{", "internal: expected '{' at start index"
    depth = 0
    in_str = False
    escape = False
    for i in range(start, len(text)):
        ch = text[i]
        if in_str:
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
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
                    return text[start : i + 1]
    raise AssertionError("Could not find a balanced JSON object inside the HTML.")


def _extract_vega_lite_spec(html: str) -> dict[str, Any]:
    # Altair's HTML embeds a call like `vegaEmbed("#vis", {...}, {...})`.
    match = re.search(r"vegaEmbed\s*\(\s*['\"][^'\"]+['\"]\s*,\s*", html)
    assert match is not None, (
        "Could not find a `vegaEmbed(\"#...\", <spec>, ...)` call in the HTML. "
        "The chart must be saved via Altair's HTML save path."
    )
    spec_start = match.end()
    assert spec_start < len(html) and html[spec_start] == "{", (
        "Expected the second argument to `vegaEmbed` to be a JSON object literal."
    )
    spec_text = _balanced_json_object(html, spec_start)
    try:
        spec = json.loads(spec_text)
    except json.JSONDecodeError as exc:
        raise AssertionError(
            f"The embedded Vega-Lite spec is not valid JSON: {exc}. "
            f"First 200 chars: {spec_text[:200]!r}"
        ) from exc
    assert isinstance(spec, dict), "Expected the embedded Vega-Lite spec to be a JSON object."
    return spec


# ---------------------------------------------------------------------------
# Generic recursive traversal helpers
# ---------------------------------------------------------------------------


def _walk(node: Any):
    """Yield every dict / list / scalar contained in `node`, recursively."""
    yield node
    if isinstance(node, dict):
        for v in node.values():
            yield from _walk(v)
    elif isinstance(node, list):
        for v in node:
            yield from _walk(v)


def _all_dicts(spec: dict[str, Any]):
    for node in _walk(spec):
        if isinstance(node, dict):
            yield node


def _collect_marks(spec: dict[str, Any]) -> list[str]:
    marks: list[str] = []
    for node in _all_dicts(spec):
        mark = node.get("mark")
        if isinstance(mark, str):
            marks.append(mark)
        elif isinstance(mark, dict):
            t = mark.get("type")
            if isinstance(t, str):
                marks.append(t)
    return marks


def _collect_transforms(spec: dict[str, Any]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for node in _all_dicts(spec):
        ts = node.get("transform")
        if isinstance(ts, list):
            for t in ts:
                if isinstance(t, dict):
                    out.append(t)
    return out


def _collect_params(spec: dict[str, Any]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for node in _all_dicts(spec):
        # Vega-Lite v5 uses "params", legacy used "selection".
        for key in ("params", "selection"):
            ps = node.get(key)
            if isinstance(ps, list):
                for p in ps:
                    if isinstance(p, dict):
                        out.append(p)
            elif isinstance(ps, dict):
                # legacy "selection" was an object map
                for name, body in ps.items():
                    if isinstance(body, dict):
                        merged = {"name": name, **body}
                        out.append(merged)
    return out


def _collect_color_encodings(spec: dict[str, Any]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for node in _all_dicts(spec):
        enc = node.get("encoding")
        if isinstance(enc, dict):
            color = enc.get("color")
            if isinstance(color, dict):
                out.append(color)
    return out


def _collect_tooltip_encodings(spec: dict[str, Any]) -> list[Any]:
    out: list[Any] = []
    for node in _all_dicts(spec):
        enc = node.get("encoding")
        if isinstance(enc, dict) and "tooltip" in enc:
            out.append(enc["tooltip"])
    return out


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def html_text() -> str:
    return _read_html()


@pytest.fixture(scope="session")
def vega_spec(html_text: str) -> dict[str, Any]:
    return _extract_vega_lite_spec(html_text)


@pytest.fixture(scope="session")
def serve_chart(xprocess):
    class Starter(ProcessStarter):
        name = "serve_chart"
        args = ["python3", "-m", "http.server", str(SERVE_PORT)]
        env = os.environ.copy()
        popen_kwargs = {
            "cwd": PROJECT_DIR,
            "text": True,
        }
        timeout = 60
        terminate_on_interrupt = True

        def startup_check(self):
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                return s.connect_ex(("localhost", SERVE_PORT)) == 0

    xprocess.ensure(Starter.name, Starter)
    yield SERVE_URL
    info = xprocess.getinfo(Starter.name)
    info.terminate()


# ---------------------------------------------------------------------------
# Verification tests (one per truth condition)
# ---------------------------------------------------------------------------


def test_chart_html_exists_and_non_empty(html_text: str):
    # _read_html already asserted existence + non-empty.
    assert "vegaEmbed" in html_text or "vega-embed" in html_text, (
        "Expected the produced HTML to reference Vega-Embed (Altair's default save_html). "
        "Found neither 'vegaEmbed' nor 'vega-embed' in the file."
    )


def test_embedded_spec_is_vega_lite(vega_spec: dict[str, Any]):
    schema = vega_spec.get("$schema", "")
    assert isinstance(schema, str) and "vega-lite" in schema.lower(), (
        f"Expected the embedded spec to declare a vega-lite $schema, got: {schema!r}"
    )


def test_spec_contains_geoshape_mark(vega_spec: dict[str, Any]):
    marks = _collect_marks(vega_spec)
    assert "geoshape" in marks, (
        f"Expected the spec to contain at least one `geoshape` mark, got marks={marks!r}"
    )


def test_spec_declares_albers_usa_projection(vega_spec: dict[str, Any]):
    found = False
    for node in _all_dicts(vega_spec):
        proj = node.get("projection")
        if isinstance(proj, dict) and proj.get("type") == "albersUsa":
            found = True
            break
    assert found, (
        "Expected the spec to declare `projection: {type: 'albersUsa'}` on the chart "
        "or one of its sub-views."
    )


def test_spec_has_lookup_transform_on_id_for_population_dataset(vega_spec: dict[str, Any]):
    transforms = _collect_transforms(vega_spec)
    lookup_matches = []
    for t in transforms:
        if "lookup" not in t or "from" not in t:
            continue
        frm = t["from"]
        if not isinstance(frm, dict):
            continue
        data = frm.get("data")
        url = ""
        if isinstance(data, dict):
            url = str(data.get("url", ""))
        # The lookup must key on 'id'.
        if frm.get("key") != "id":
            continue
        if POPULATION_DATASET_HINT not in url:
            continue
        lookup_matches.append(t)
    assert lookup_matches, (
        "Expected a `lookup` transform whose `from.data.url` references the "
        f"{POPULATION_DATASET_HINT!r} dataset and whose `from.key` is 'id'. "
        f"Found transforms: {transforms!r}"
    )

    # Among matching lookups, the combined `fields` list must include all three metrics
    # AND a state-name field that the tooltip can use.
    combined_fields: set[str] = set()
    for t in lookup_matches:
        frm = t["from"]
        fields = frm.get("fields")
        if isinstance(fields, list):
            combined_fields.update(str(f) for f in fields)

    for metric in METRIC_OPTIONS:
        assert metric in combined_fields, (
            f"Expected the lookup transform(s) to import the {metric!r} field from "
            f"{POPULATION_DATASET_HINT!r}, got fields={sorted(combined_fields)!r}."
        )
    assert "state" in combined_fields, (
        "Expected the lookup transform(s) to import a 'state' name field for the tooltip, "
        f"got fields={sorted(combined_fields)!r}."
    )


def test_spec_has_binding_select_param_with_three_metric_options(vega_spec: dict[str, Any]):
    params = _collect_params(vega_spec)
    matching = []
    for p in params:
        bind = p.get("bind")
        if not isinstance(bind, dict):
            continue
        if bind.get("input") != "select":
            continue
        options = bind.get("options")
        if isinstance(options, list) and [str(o) for o in options] == METRIC_OPTIONS:
            matching.append(p)
    assert matching, (
        "Expected a parameter whose binding is `{input: 'select', options: "
        f"{METRIC_OPTIONS}}}` (order matters). Found params: {params!r}"
    )


def test_spec_resolves_dynamic_metric(vega_spec: dict[str, Any]):
    """The chosen metric must be resolved either via a `calculate` transform that
    references the binding-select parameter, OR via three layers each filtered by
    one of the three metric names."""
    params = _collect_params(vega_spec)
    param_names: list[str] = []
    for p in params:
        bind = p.get("bind")
        if isinstance(bind, dict) and bind.get("input") == "select":
            options = bind.get("options")
            if isinstance(options, list) and [str(o) for o in options] == METRIC_OPTIONS:
                name = p.get("name")
                if isinstance(name, str):
                    param_names.append(name)
    assert param_names, "Could not identify the metric-select parameter name."

    transforms = _collect_transforms(vega_spec)

    # Option A: a `calculate` transform expression that references the parameter name.
    calc_refs_param = False
    for t in transforms:
        if "calculate" in t and isinstance(t["calculate"], str):
            expr = t["calculate"]
            if any(name in expr for name in param_names):
                calc_refs_param = True
                break

    # Option B: three filter-transforms, one per metric.
    metric_filter_hits = {m: False for m in METRIC_OPTIONS}
    for t in transforms:
        f = t.get("filter")
        if isinstance(f, str):
            for m in METRIC_OPTIONS:
                if (
                    f"'{m}'" in f
                    or f'"{m}"' in f
                    or any(f"{n} == '{m}'" in f or f'{n} == "{m}"' in f for n in param_names)
                ):
                    metric_filter_hits[m] = True
        elif isinstance(f, dict):
            # alt.FieldEqualPredicate-style
            equal = f.get("equal")
            if isinstance(equal, str) and equal in METRIC_OPTIONS:
                metric_filter_hits[equal] = True
    three_filtered_layers = all(metric_filter_hits.values())

    assert calc_refs_param or three_filtered_layers, (
        "Expected either a `calculate` transform whose expression references the "
        f"metric-select parameter (names={param_names!r}), OR three `filter` transforms "
        f"covering each of {METRIC_OPTIONS!r}. Found neither. "
        f"Transforms: {transforms!r}"
    )


def test_color_encoding_is_quantitative(vega_spec: dict[str, Any]):
    color_encodings = _collect_color_encodings(vega_spec)
    assert color_encodings, "Expected at least one `color` encoding in the spec."
    assert any(c.get("type") == "quantitative" for c in color_encodings), (
        f"Expected at least one quantitative color encoding, got: {color_encodings!r}"
    )


def test_tooltip_has_state_name_and_metric_value(vega_spec: dict[str, Any]):
    tooltip_encodings = _collect_tooltip_encodings(vega_spec)
    assert tooltip_encodings, "Expected at least one `tooltip` encoding in the spec."

    # Tooltip can be a list of channel objects, or a single channel object.
    flat: list[dict[str, Any]] = []
    for tt in tooltip_encodings:
        if isinstance(tt, list):
            flat.extend(x for x in tt if isinstance(x, dict))
        elif isinstance(tt, dict):
            flat.append(tt)

    has_name = any(
        ch.get("type") == "nominal"
        and isinstance(ch.get("field"), str)
        and "state" in ch["field"].lower()
        for ch in flat
    )
    has_value = any(ch.get("type") == "quantitative" for ch in flat)

    assert has_name, (
        f"Expected the tooltip to include a nominal field referring to the state name, "
        f"got tooltip channels: {flat!r}"
    )
    assert has_value, (
        f"Expected the tooltip to include a quantitative field for the metric value, "
        f"got tooltip channels: {flat!r}"
    )


# ---------------------------------------------------------------------------
# Browser verification
# ---------------------------------------------------------------------------


def test_browser_renders_map_and_dropdown(serve_chart):
    verifier = PochiVerifier()
    reason = (
        "The chart.html produced by the build script must render an interactive US "
        "state-level choropleth map together with a dropdown that switches the displayed "
        "metric among the three columns of the population_engineers_hurricanes dataset."
    )
    truth = (
        f"Navigate to {serve_chart}. Wait for the Vega-Embed chart to finish rendering. "
        "Then verify two things: "
        "(1) the page shows a US-shaped map made of many SVG path elements (at least 40 "
        "non-empty <path> elements should be present inside the chart container, one per "
        "US state). "
        "(2) the page exposes exactly one <select> dropdown control whose three <option> "
        "elements, in document order, have text content equal to 'population', 'engineers', "
        "and 'hurricanes' (case-sensitive, exact match, no other options). "
        "Both conditions must hold for the verification to pass."
    )
    result = verifier.verify(
        reason=reason,
        truth=truth,
        use_browser_agent=True,
        trajectory_dir="/logs/verifier/pochi/test_browser_renders_map_and_dropdown",
    )
    assert result.status == "pass", f"Browser verification failed: {result.reason}"
