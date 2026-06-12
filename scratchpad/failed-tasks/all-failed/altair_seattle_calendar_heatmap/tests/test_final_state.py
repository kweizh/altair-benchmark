import json
import os
import re
import socket
import subprocess
import sys
from typing import Any, Optional

import pytest
from pochi_verifier import PochiVerifier
from xprocess import ProcessStarter

PROJECT_DIR = "/home/user/myproject"
CHART_HTML = os.path.join(PROJECT_DIR, "chart.html")
HTTP_PORT = 8765
CHART_URL = f"http://localhost:{HTTP_PORT}/chart.html"

EXPECTED_YEARS = {2012, 2013, 2014, 2015}


# ---------------------------------------------------------------------------
# Helpers for parsing the embedded Vega-Lite spec
# ---------------------------------------------------------------------------


def _read_chart_html() -> str:
    assert os.path.isfile(CHART_HTML), (
        f"Expected generated chart at {CHART_HTML}, but the file is missing."
    )
    with open(CHART_HTML, "r", encoding="utf-8") as fh:
        text = fh.read()
    assert text.strip(), "chart.html exists but is empty."
    return text


def _extract_spec(html: str) -> dict:
    """Pull the first embedded Vega-Lite JSON spec out of the HTML."""
    # Search for the first occurrence of the Vega-Lite schema marker and walk
    # backwards / forwards to capture a balanced JSON object.
    schema_marker = re.search(r'"\$schema"\s*:\s*"https?://vega\.github\.io/schema/vega-lite/', html)
    assert schema_marker is not None, (
        "Embedded Vega-Lite spec (with $schema marker) not found in chart.html."
    )

    # Find the '{' that opens the JSON object containing this $schema field.
    start = html.rfind("{", 0, schema_marker.start())
    assert start != -1, "Could not locate start of embedded JSON spec."

    depth = 0
    in_str = False
    escape = False
    end = -1
    for i in range(start, len(html)):
        ch = html[i]
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
                    end = i + 1
                    break
    assert end != -1, "Could not find closing brace of embedded JSON spec."
    raw = html[start:end]
    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        raise AssertionError(f"Embedded spec is not valid JSON: {exc}") from None


def _iter_specs(spec: dict):
    """Yield the top-level spec and any nested unit specs (facet/repeat/concat/layer/hconcat/vconcat)."""
    yield spec
    for key in ("spec",):
        if isinstance(spec.get(key), dict):
            yield from _iter_specs(spec[key])
    for key in ("layer", "concat", "hconcat", "vconcat"):
        for sub in spec.get(key, []) or []:
            if isinstance(sub, dict):
                yield from _iter_specs(sub)


def _find_unit_spec_with_rect(spec: dict) -> Optional[dict]:
    for sub in _iter_specs(spec):
        mark = sub.get("mark")
        if isinstance(mark, str) and mark == "rect":
            return sub
        if isinstance(mark, dict) and mark.get("type") == "rect":
            return sub
    return None


# ---------------------------------------------------------------------------
# File-level checks
# ---------------------------------------------------------------------------


def test_chart_html_exists_and_embeds_vega_lite():
    html = _read_chart_html()
    assert "vegaEmbed(" in html, "chart.html does not call vegaEmbed(); is this an Altair HTML export?"
    assert re.search(r'vega\.github\.io/schema/vega-lite/', html), (
        "chart.html does not reference a Vega-Lite schema URL."
    )


# ---------------------------------------------------------------------------
# Spec-shape checks
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def spec() -> dict:
    return _extract_spec(_read_chart_html())


@pytest.fixture(scope="module")
def rect_spec(spec) -> dict:
    sub = _find_unit_spec_with_rect(spec)
    assert sub is not None, (
        "Could not find a unit spec using mark=rect. The calendar heatmap must use mark_rect."
    )
    return sub


def test_spec_uses_rect_mark(rect_spec):
    mark = rect_spec["mark"]
    mark_type = mark if isinstance(mark, str) else mark.get("type")
    assert mark_type == "rect", f"Expected mark='rect', got {mark!r}."


def test_x_encoding_is_day_of_month(rect_spec):
    enc = rect_spec.get("encoding", {})
    x = enc.get("x")
    assert isinstance(x, dict), "Missing x encoding on the rect mark."
    assert x.get("field") == "date", f"x encoding must use the 'date' field, got {x.get('field')!r}."
    assert x.get("timeUnit") == "date", (
        f"x encoding must use timeUnit='date' (day-of-month), got {x.get('timeUnit')!r}."
    )
    assert x.get("type") == "ordinal", (
        f"x encoding must be ordinal (use ':O' shorthand), got type={x.get('type')!r}."
    )


def test_y_encoding_is_month(rect_spec):
    enc = rect_spec.get("encoding", {})
    y = enc.get("y")
    assert isinstance(y, dict), "Missing y encoding on the rect mark."
    assert y.get("field") == "date", f"y encoding must use the 'date' field, got {y.get('field')!r}."
    assert y.get("timeUnit") == "month", (
        f"y encoding must use timeUnit='month', got {y.get('timeUnit')!r}."
    )
    assert y.get("type") == "ordinal", (
        f"y encoding must be ordinal (use ':O' shorthand), got type={y.get('type')!r}."
    )


def test_color_is_sum_precipitation_with_greens_scheme(rect_spec):
    enc = rect_spec.get("encoding", {})
    color = enc.get("color")
    assert isinstance(color, dict), "Missing color encoding on the rect mark."
    assert color.get("field") == "precipitation", (
        f"color encoding must use field='precipitation', got {color.get('field')!r}."
    )
    assert color.get("aggregate") == "sum", (
        f"color encoding must aggregate with sum, got {color.get('aggregate')!r}."
    )
    assert color.get("type") == "quantitative", (
        f"color encoding must be quantitative, got type={color.get('type')!r}."
    )
    scale = color.get("scale")
    assert isinstance(scale, dict), "color encoding must define a scale with scheme='greens'."
    assert scale.get("scheme") == "greens", (
        f"color scale scheme must be 'greens', got {scale.get('scheme')!r}."
    )


def test_facet_or_repeat_by_year(spec, rect_spec):
    """Either the wrapping spec has a facet/repeat by year(date), or the unit spec uses a facet/column/row encoding by year(date)."""

    def _matches_year_timeunit(obj: Any) -> bool:
        if not isinstance(obj, dict):
            return False
        if obj.get("field") == "date" and obj.get("timeUnit") == "year":
            return True
        return False

    # 1. Faceted via top-level facet / repeat
    for sub in _iter_specs(spec):
        facet = sub.get("facet")
        if isinstance(facet, dict):
            # FacetChart with {row,column} mapping or single facet definition
            if _matches_year_timeunit(facet):
                return
            for axis in ("row", "column"):
                if _matches_year_timeunit(facet.get(axis)):
                    return
        repeat = sub.get("repeat")
        if isinstance(repeat, dict) or isinstance(repeat, list):
            # RepeatChart - look for "year(date)" string in the repeat list
            flat = json.dumps(repeat)
            if "year(date)" in flat or "year_date" in flat:
                return

    # 2. Faceted via encoding channel on the unit spec (facet / column / row)
    enc = rect_spec.get("encoding", {})
    for axis in ("facet", "column", "row"):
        if _matches_year_timeunit(enc.get(axis)):
            return

    pytest.fail(
        "Spec must facet or repeat panels by year(date); did not find a facet/repeat/column/row "
        "with field='date' and timeUnit='year'."
    )


def _collect_params(spec: dict) -> list:
    found: list = []
    for sub in _iter_specs(spec):
        for p in sub.get("params", []) or []:
            if isinstance(p, dict):
                found.append(p)
    return found


def test_binding_select_year_param(spec):
    params = _collect_params(spec)
    select_params = [
        p for p in params
        if isinstance(p.get("bind"), dict) and p["bind"].get("input") == "select"
    ]
    assert len(select_params) == 1, (
        f"Expected exactly one params entry bound to binding_select, found {len(select_params)}."
    )
    bind = select_params[0]["bind"]
    options = bind.get("options")
    assert isinstance(options, list), "binding_select must define an 'options' list."
    coerced = set()
    for opt in options:
        try:
            coerced.add(int(opt))
        except (TypeError, ValueError):
            pass
    missing = EXPECTED_YEARS - coerced
    assert not missing, (
        f"binding_select options must include the years {sorted(EXPECTED_YEARS)}, missing: {sorted(missing)}."
    )


def test_opacity_is_conditional_on_year_param(spec, rect_spec):
    params = _collect_params(spec)
    select_params = [
        p for p in params
        if isinstance(p.get("bind"), dict) and p["bind"].get("input") == "select"
    ]
    assert select_params, "Cannot evaluate opacity condition without a binding_select param."
    param_name = select_params[0].get("name")
    assert param_name, "binding_select param must have a name."

    # Walk every unit spec for an opacity encoding referencing this param.
    found_condition = False
    for sub in _iter_specs(spec):
        enc = sub.get("encoding")
        if not isinstance(enc, dict):
            continue
        opacity = enc.get("opacity")
        if not isinstance(opacity, dict):
            continue
        condition = opacity.get("condition")
        if condition is None:
            continue
        condition_blob = json.dumps(condition)
        if param_name in condition_blob:
            found_condition = True
            break

    assert found_condition, (
        f"Opacity encoding must be a conditional encoding driven by the bound param "
        f"{param_name!r} (alt.when(... == {param_name}).then(1).otherwise(0.2))."
    )


def test_tooltip_includes_date_and_sum_precipitation(rect_spec):
    enc = rect_spec.get("encoding", {})
    tooltip = enc.get("tooltip")
    assert tooltip is not None, "Missing tooltip encoding on the rect mark."
    items = tooltip if isinstance(tooltip, list) else [tooltip]
    blob = json.dumps(items)
    assert '"field": "date"' in blob or '"field":"date"' in blob, (
        "Tooltip must include the 'date' field."
    )
    has_precip_sum = any(
        isinstance(t, dict)
        and t.get("field") == "precipitation"
        and t.get("aggregate") == "sum"
        for t in items
    )
    assert has_precip_sum, "Tooltip must include the summed precipitation."


# ---------------------------------------------------------------------------
# Browser verification with pochi-verifier
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def http_server(xprocess):
    class Starter(ProcessStarter):
        name = "altair_http_server"
        args = [sys.executable, "-m", "http.server", str(HTTP_PORT)]
        env = os.environ.copy()
        popen_kwargs = {
            "cwd": PROJECT_DIR,
            "text": True,
        }
        timeout = 60
        terminate_on_interrupt = True

        def startup_check(self):
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                return s.connect_ex(("localhost", HTTP_PORT)) == 0

    xprocess.ensure(Starter.name, Starter)
    yield
    info = xprocess.getinfo(Starter.name)
    info.terminate()


def test_browser_render(http_server):
    reason = (
        "The Altair-generated chart.html should render a Seattle precipitation calendar heatmap "
        "with one panel per year (2012-2015), a 12-row by ~31-column grid of green-shaded rect "
        "cells in each panel, and an HTML dropdown bound to the year that visibly dims the "
        "non-selected yearly panels."
    )
    truth = (
        f"Navigate to {CHART_URL} and wait for the Vega-Embed rendering to complete. "
        "Verify that the page shows at least 4 faceted yearly panels (one for each of 2012, 2013, "
        "2014 and 2015). Each panel should contain a dense grid of rectangular cells arranged in "
        "12 rows (months) by roughly 31 columns (days of month), shaded with a green color scale "
        "(scheme='greens'). Verify that an HTML <select> dropdown is present on the page (the "
        "year selector bound via binding_select). When a year is selected in the dropdown, the "
        "panel for that year should appear at full opacity while the other yearly panels are "
        "visibly dimmed (lower opacity). Tooltips over a cell should show the date and the "
        "summed precipitation."
    )

    verifier = PochiVerifier()
    result = verifier.verify(
        reason=reason,
        truth=truth,
        use_browser_agent=True,
        trajectory_dir="/logs/verifier/pochi/test_browser_render",
    )
    assert result.status == "pass", f"Browser verification failed: {result.reason}"
