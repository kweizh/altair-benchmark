import json
import os
import socket
from typing import Any

import pytest
from xprocess import ProcessStarter

from pochi_verifier import PochiVerifier

PROJECT_DIR = "/home/user/myproject"
CHART_HTML = os.path.join(PROJECT_DIR, "chart.html")
CHART_JSON = os.path.join(PROJECT_DIR, "chart.json")

PREVIEW_PORT = 8765
PREVIEW_URL = f"http://localhost:{PREVIEW_PORT}/chart.html"


# ---------------------------------------------------------------------------
# Helpers for digging into the Vega-Lite spec produced by Altair.
# ---------------------------------------------------------------------------


def _load_spec() -> dict[str, Any]:
    assert os.path.isfile(CHART_JSON), (
        f"Vega-Lite spec file not found at {CHART_JSON}; the task must save the "
        f"chart specification (e.g. via chart.to_dict() / chart.to_json())."
    )
    with open(CHART_JSON, "r", encoding="utf-8") as f:
        text = f.read()
    try:
        spec = json.loads(text)
    except json.JSONDecodeError as exc:
        raise AssertionError(
            f"{CHART_JSON} is not valid JSON: {exc}"
        ) from exc
    assert isinstance(spec, dict), (
        f"Expected the spec in {CHART_JSON} to be a JSON object, got {type(spec).__name__}."
    )
    return spec


def _inner_spec(spec: dict[str, Any]) -> dict[str, Any]:
    """Return the spec that holds the mark/encoding/params for a facet chart.

    Altair emits either:
      { "facet": {...}, "spec": { mark, encoding, params, ... } }
    or, when using the `column` encoding channel, the params/encoding live at the
    top level. We accept both.
    """
    if isinstance(spec.get("spec"), dict):
        return spec["spec"]
    return spec


def _find_facet_column_field(spec: dict[str, Any]) -> str | None:
    # Pattern 1: top-level facet block from .facet(column=...)
    facet = spec.get("facet")
    if isinstance(facet, dict):
        column = facet.get("column")
        if isinstance(column, dict) and isinstance(column.get("field"), str):
            return column["field"]
        # facet may directly be the field spec when only one channel
        if isinstance(facet.get("field"), str):
            return facet["field"]

    # Pattern 2: column encoding inside the inner spec
    inner = _inner_spec(spec)
    encoding = inner.get("encoding")
    if isinstance(encoding, dict):
        column = encoding.get("column")
        if isinstance(column, dict) and isinstance(column.get("field"), str):
            return column["field"]
    return None


def _find_legend_point_param(spec: dict[str, Any]) -> dict[str, Any] | None:
    candidates: list[dict[str, Any]] = []
    for container in (spec, _inner_spec(spec)):
        params = container.get("params")
        if isinstance(params, list):
            for p in params:
                if isinstance(p, dict):
                    candidates.append(p)

    for p in candidates:
        select = p.get("select")
        select_type = None
        select_fields: list[str] = []
        if isinstance(select, dict):
            select_type = select.get("type")
            fields = select.get("fields")
            if isinstance(fields, list):
                select_fields = [str(f) for f in fields]
        elif isinstance(select, str):
            select_type = select

        if select_type != "point":
            continue
        if "Species" not in select_fields:
            continue

        bind = p.get("bind")
        bind_is_legend = bind == "legend" or (
            isinstance(bind, dict) and "legend" in bind
        )
        if not bind_is_legend:
            continue
        return p
    return None


# ---------------------------------------------------------------------------
# Spec-level assertions (no browser required).
# ---------------------------------------------------------------------------


def test_chart_html_exists():
    assert os.path.isfile(CHART_HTML), (
        f"Expected the rendered chart HTML at {CHART_HTML}, but it is missing."
    )


def test_chart_json_exists():
    assert os.path.isfile(CHART_JSON), (
        f"Expected the Vega-Lite specification at {CHART_JSON}, but it is missing."
    )


def test_facet_uses_island_column():
    spec = _load_spec()
    field = _find_facet_column_field(spec)
    assert field == "Island", (
        f"Expected the chart to be faceted by column on field 'Island', got "
        f"{field!r}. The spec must contain a facet/column whose field is 'Island'."
    )


def test_legend_bound_point_selection_on_species():
    spec = _load_spec()
    param = _find_legend_point_param(spec)
    assert param is not None, (
        "Expected a point selection (param) projected over the 'Species' field "
        "and bound to the legend (bind == 'legend' or bind == {'legend': ...}). "
        "None of the params in the spec match."
    )
    # Sanity: name must be a non-empty string so the opacity condition can reference it.
    assert isinstance(param.get("name"), str) and param["name"], (
        f"Legend-bound point selection must have a non-empty 'name'; got {param!r}."
    )


def test_opacity_encoding_is_condition_on_selection():
    spec = _load_spec()
    inner = _inner_spec(spec)
    encoding = inner.get("encoding")
    assert isinstance(encoding, dict), (
        "Inner spec is missing the 'encoding' block."
    )
    opacity = encoding.get("opacity")
    assert isinstance(opacity, dict), (
        "Encoding must define an 'opacity' channel driven by the legend selection."
    )

    param = _find_legend_point_param(spec)
    assert param is not None, (
        "Legend-bound point selection was not found while checking opacity."
    )
    param_name = param["name"]

    condition = opacity.get("condition")
    assert isinstance(condition, dict), (
        f"'opacity' must use a 'condition' block referencing the selection param "
        f"{param_name!r}; got {opacity!r}."
    )
    assert condition.get("param") == param_name, (
        f"'opacity.condition.param' must reference the legend-bound param "
        f"{param_name!r}; got {condition.get('param')!r}."
    )

    # Selected branch: high opacity (~1).
    selected_value = condition.get("value")
    assert isinstance(selected_value, (int, float)), (
        f"opacity.condition.value must be numeric; got {selected_value!r}."
    )
    assert 0.9 <= float(selected_value) <= 1.0, (
        f"Selected opacity should be ~1.0 (fully opaque); got {selected_value!r}."
    )

    # Otherwise branch: low opacity (~0.1, in any case strictly less than 0.5).
    otherwise_value = opacity.get("value")
    assert isinstance(otherwise_value, (int, float)), (
        f"'opacity.value' (the otherwise branch) must be numeric; got {otherwise_value!r}."
    )
    assert 0.0 <= float(otherwise_value) < 0.5, (
        f"Unselected opacity should be low (~0.1, definitely < 0.5); got "
        f"{otherwise_value!r}."
    )


def test_resolve_scale_y_independent():
    spec = _load_spec()
    resolve = spec.get("resolve")
    assert isinstance(resolve, dict), (
        "Spec must include a top-level 'resolve' block configuring scale resolution."
    )
    scale = resolve.get("scale")
    assert isinstance(scale, dict), (
        f"'resolve.scale' must be an object; got {scale!r}."
    )
    assert scale.get("y") == "independent", (
        f"Expected 'resolve.scale.y' to be 'independent' so each facet panel has "
        f"its own y-axis; got {scale.get('y')!r}."
    )


def test_axis_scales_disable_zero():
    spec = _load_spec()
    inner = _inner_spec(spec)
    encoding = inner.get("encoding")
    assert isinstance(encoding, dict), "Inner spec is missing the 'encoding' block."

    for channel in ("x", "y"):
        channel_def = encoding.get(channel)
        assert isinstance(channel_def, dict), (
            f"Encoding channel {channel!r} is missing or not an object."
        )
        scale = channel_def.get("scale")
        assert isinstance(scale, dict), (
            f"Encoding channel {channel!r} must define a 'scale' block with zero=False; "
            f"got {scale!r}."
        )
        assert scale.get("zero") is False, (
            f"Encoding channel {channel!r} must set scale.zero to false; got "
            f"{scale.get('zero')!r}."
        )


def test_core_encodings_use_expected_fields():
    spec = _load_spec()
    inner = _inner_spec(spec)
    encoding = inner.get("encoding")
    assert isinstance(encoding, dict), "Inner spec is missing the 'encoding' block."

    expected = {
        "x": "Beak Length (mm)",
        "y": "Body Mass (g)",
        "color": "Species",
    }
    for channel, field in expected.items():
        channel_def = encoding.get(channel)
        assert isinstance(channel_def, dict), (
            f"Encoding channel {channel!r} is missing."
        )
        assert channel_def.get("field") == field, (
            f"Encoding channel {channel!r} must use field {field!r}; got "
            f"{channel_def.get('field')!r}."
        )


# ---------------------------------------------------------------------------
# Browser verification — serve the HTML over a local HTTP server, then ask
# pochi-verifier to inspect facet panels and the clickable legend.
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def serve_chart(xprocess):
    class Starter(ProcessStarter):
        name = "serve_chart"
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
    yield PREVIEW_URL
    info = xprocess.getinfo(Starter.name)
    info.terminate()


@pytest.fixture(scope="session")
def browser_verifier():
    yield PochiVerifier()


def test_browser_shows_facets_and_clickable_legend(serve_chart, browser_verifier):
    reason = (
        "The chart at chart.html must render a faceted scatter of Palmer penguins "
        "(Beak Length vs Body Mass), with one panel per Island, colored by Species, "
        "and an interactive legend that lets the viewer toggle species visibility "
        "across all facet panels."
    )
    truth = (
        f"Navigate to {PREVIEW_URL}. Wait for the Vega/Altair chart to finish "
        "rendering (the SVG/canvas produced by vegaEmbed should be visible). "
        "Then verify all of the following: "
        "(1) At least 3 distinct facet panels are rendered side-by-side, one per "
        "island value; each panel shows its own scatter of points. "
        "(2) A legend for 'Species' is visible next to the chart, listing the "
        "species categories. "
        "(3) The legend entries are interactive: hovering a legend symbol shows "
        "a pointer cursor, and clicking a legend entry visibly changes the "
        "opacity of the matching points across ALL facet panels (selected "
        "species stay fully opaque, the other species fade to a low opacity)."
    )
    result = browser_verifier.verify(
        reason=reason,
        truth=truth,
        use_browser_agent=True,
        trajectory_dir="/logs/verifier/pochi/test_browser_shows_facets_and_clickable_legend",
    )
    assert result.status == "pass", (
        f"Browser verification failed: {result.reason}"
    )
