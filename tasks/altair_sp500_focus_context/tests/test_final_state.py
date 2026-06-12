import json
import os
import re
import socket
import subprocess
from typing import Any

import pytest
from xprocess import ProcessStarter

PROJECT_DIR = "/home/user/altair_project"
CHART_HTML = os.path.join(PROJECT_DIR, "chart.html")
BUILD_SCRIPT = os.path.join(PROJECT_DIR, "build_chart.py")
SERVER_PORT = 8765


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _build_chart() -> None:
    """Run the executor's build script to regenerate the saved chart."""
    if os.path.exists(CHART_HTML):
        os.remove(CHART_HTML)
    result = subprocess.run(
        ["python3", BUILD_SCRIPT],
        capture_output=True,
        text=True,
        cwd=PROJECT_DIR,
    )
    assert result.returncode == 0, (
        f"Running build_chart.py failed: stdout={result.stdout!r} "
        f"stderr={result.stderr!r}"
    )


def _extract_spec(html: str) -> dict[str, Any]:
    """Extract the embedded Vega-Lite JSON spec from an Altair-saved HTML file."""
    # Altair's default template embeds the spec as: var spec = { ... };
    match = re.search(r"var\s+spec\s*=\s*(\{.*?\})\s*;\s*var\s+embedOpt", html, re.DOTALL)
    if match is None:
        # Fallback: look for vegaEmbed("#vis", { ... }
        match = re.search(r"vegaEmbed\([^,]+,\s*(\{.*?\})\s*,", html, re.DOTALL)
    assert match is not None, (
        "Could not locate the embedded Vega-Lite JSON spec inside chart.html."
    )
    raw = match.group(1)
    return json.loads(raw)


def _iter_specs(node: Any):
    """Recursively yield every dict in a Vega-Lite spec tree."""
    if isinstance(node, dict):
        yield node
        for v in node.values():
            yield from _iter_specs(v)
    elif isinstance(node, list):
        for item in node:
            yield from _iter_specs(item)


def _mark_type(spec: dict[str, Any]) -> str | None:
    mark = spec.get("mark")
    if isinstance(mark, str):
        return mark
    if isinstance(mark, dict):
        t = mark.get("type")
        if isinstance(t, str):
            return t
    return None


def _has_mark_in_tree(spec: dict[str, Any], mark_name: str) -> bool:
    for node in _iter_specs(spec):
        if _mark_type(node) == mark_name:
            return True
    return False


def _has_area_mark(spec: dict[str, Any]) -> bool:
    return _has_mark_in_tree(spec, "area")


def _find_brush_param_name(spec: dict[str, Any]) -> str | None:
    """Locate a parameter whose select is an interval restricted to the x encoding."""
    for node in _iter_specs(spec):
        params = node.get("params") if isinstance(node, dict) else None
        if not isinstance(params, list):
            continue
        for p in params:
            if not isinstance(p, dict):
                continue
            select = p.get("select")
            if isinstance(select, str) and select == "interval":
                # Without explicit encodings restriction; skip.
                continue
            if isinstance(select, dict):
                if select.get("type") != "interval":
                    continue
                encodings = select.get("encodings")
                if isinstance(encodings, list) and encodings == ["x"]:
                    name = p.get("name")
                    if isinstance(name, str):
                        return name
    return None


def _x_scale_domain_param(spec: dict[str, Any]) -> str | None:
    """Return the param name referenced by an x-encoding's scale.domain, if any."""
    for node in _iter_specs(spec):
        encoding = node.get("encoding") if isinstance(node, dict) else None
        if not isinstance(encoding, dict):
            continue
        x = encoding.get("x")
        if not isinstance(x, dict):
            continue
        scale = x.get("scale")
        if not isinstance(scale, dict):
            continue
        domain = scale.get("domain")
        if isinstance(domain, dict):
            param = domain.get("param")
            if isinstance(param, str):
                return param
    return None


def _filter_references_param(filter_obj: Any, brush_name: str) -> bool:
    if isinstance(filter_obj, dict):
        if filter_obj.get("param") == brush_name:
            return True
        return any(_filter_references_param(v, brush_name) for v in filter_obj.values())
    if isinstance(filter_obj, list):
        return any(_filter_references_param(v, brush_name) for v in filter_obj)
    if isinstance(filter_obj, str):
        return brush_name in filter_obj
    return False


def _has_brush_filter(spec: dict[str, Any], brush_name: str) -> bool:
    for node in _iter_specs(spec):
        transforms = node.get("transform") if isinstance(node, dict) else None
        if not isinstance(transforms, list):
            continue
        for t in transforms:
            if not isinstance(t, dict):
                continue
            if "filter" in t and _filter_references_param(t["filter"], brush_name):
                return True
    return False


def _has_max_price_window_or_aggregate(spec: dict[str, Any]) -> bool:
    for node in _iter_specs(spec):
        transforms = node.get("transform") if isinstance(node, dict) else None
        if not isinstance(transforms, list):
            continue
        for t in transforms:
            if not isinstance(t, dict):
                continue
            window = t.get("window")
            if isinstance(window, list):
                for w in window:
                    if (
                        isinstance(w, dict)
                        and w.get("op") == "max"
                        and w.get("field") == "price"
                    ):
                        return True
            aggregate = t.get("aggregate")
            if isinstance(aggregate, list):
                for a in aggregate:
                    if (
                        isinstance(a, dict)
                        and a.get("op") == "max"
                        and a.get("field") == "price"
                    ):
                        return True
            joinaggregate = t.get("joinaggregate")
            if isinstance(joinaggregate, list):
                for j in joinaggregate:
                    if (
                        isinstance(j, dict)
                        and j.get("op") == "max"
                        and j.get("field") == "price"
                    ):
                        return True
    return False


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def built_spec() -> dict[str, Any]:
    _build_chart()
    assert os.path.isfile(CHART_HTML), f"{CHART_HTML} was not produced by build_chart.py"
    with open(CHART_HTML, "r", encoding="utf-8") as fp:
        html = fp.read()
    assert len(html) > 0, "chart.html is empty."
    return _extract_spec(html)


@pytest.fixture(scope="session")
def static_server(xprocess):
    class Starter(ProcessStarter):
        name = "altair_chart_server"
        args = ["python3", "-m", "http.server", str(SERVER_PORT)]
        env = os.environ.copy()
        popen_kwargs = {"cwd": PROJECT_DIR, "text": True}
        timeout = 60
        terminate_on_interrupt = True

        def startup_check(self):
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                return s.connect_ex(("localhost", SERVER_PORT)) == 0

    xprocess.ensure(Starter.name, Starter)
    yield f"http://localhost:{SERVER_PORT}/chart.html"
    info = xprocess.getinfo(Starter.name)
    info.terminate()


# ---------------------------------------------------------------------------
# Spec structure tests
# ---------------------------------------------------------------------------


def test_chart_html_exists(built_spec):
    # The fixture itself rebuilds and asserts existence; just sanity check the spec.
    assert isinstance(built_spec, dict), "Extracted spec is not a JSON object."


def test_top_level_is_vconcat_of_two(built_spec):
    vconcat = built_spec.get("vconcat")
    assert isinstance(vconcat, list), (
        "Top-level spec must use vertical concatenation (a 'vconcat' field)."
    )
    assert len(vconcat) == 2, (
        f"Expected exactly two vconcat entries (upper detail + lower context); "
        f"got {len(vconcat)}."
    )


def test_both_panels_contain_area_marks(built_spec):
    vconcat = built_spec["vconcat"]
    for idx, panel in enumerate(vconcat):
        assert _has_area_mark(panel), (
            f"vconcat[{idx}] does not contain an area mark "
            f"('mark': 'area' or {{'type': 'area', ...}})."
        )


def test_lower_panel_hosts_x_interval_brush(built_spec):
    lower = built_spec["vconcat"][1]
    brush_name = _find_brush_param_name(lower)
    assert brush_name is not None, (
        "Lower (context) panel must declare a selection_interval parameter "
        "restricted to encodings=['x'] via add_params."
    )


def test_upper_panel_x_domain_bound_to_brush(built_spec):
    upper = built_spec["vconcat"][0]
    lower = built_spec["vconcat"][1]
    brush_name = _find_brush_param_name(lower)
    assert brush_name is not None, (
        "Cannot validate x-domain binding because the lower panel has no "
        "selection_interval(encodings=['x']) brush parameter."
    )
    referenced = _x_scale_domain_param(upper)
    assert referenced == brush_name, (
        f"Upper panel's x-encoding scale.domain must reference the brush parameter "
        f"'{brush_name}', but got: {referenced!r}."
    )


def test_upper_panel_has_rule_with_max_price_and_brush_filter(built_spec):
    upper = built_spec["vconcat"][0]
    lower = built_spec["vconcat"][1]
    brush_name = _find_brush_param_name(lower)
    assert brush_name is not None, "No brush parameter found for filter check."

    assert _has_mark_in_tree(upper, "rule"), (
        "Upper panel must include a 'rule' mark layered on top of the area "
        "to annotate the running maximum price."
    )
    assert _has_brush_filter(upper, brush_name), (
        f"Upper panel must contain a transform_filter referencing the brush "
        f"parameter '{brush_name}'."
    )
    assert _has_max_price_window_or_aggregate(upper), (
        "Upper panel must compute the maximum of 'price' via either "
        "transform_window(op='max', field='price'), "
        "transform_aggregate(op='max', field='price'), or "
        "transform_joinaggregate(op='max', field='price')."
    )


# ---------------------------------------------------------------------------
# Browser verification via pochi-verifier
# ---------------------------------------------------------------------------


def test_browser_renders_two_area_panels_and_brush(static_server, built_spec):
    from pochi_verifier import PochiVerifier

    reason = (
        "The saved Altair chart implements a Focus + Context dashboard on the S&P 500 "
        "price time series. The page should render two stacked filled area charts of "
        "price over time. The smaller bottom panel must support an interval brush on "
        "the x-axis, and dragging the brush should narrow the top panel's x-axis "
        "domain to the brushed window."
    )
    truth = (
        f"Navigate to {static_server}. Wait for the Vega-Lite visualization to render "
        "fully. Verify that two stacked area charts of price versus date are visible "
        "(one taller detail chart on top and a smaller context chart on the bottom). "
        "Click and drag horizontally inside the bottom (smaller) chart to create an "
        "x-axis interval brush, and verify that an interval-selection rectangle is "
        "drawn in the bottom panel and that the top panel's x-axis domain changes "
        "to reflect the brushed range."
    )

    verifier = PochiVerifier()
    result = verifier.verify(
        reason=reason,
        truth=truth,
        use_browser_agent=True,
        trajectory_dir="/logs/verifier/pochi/test_browser_renders_two_area_panels_and_brush",
    )
    assert result.status == "pass", (
        f"Browser verification failed: {getattr(result, 'reason', result)}"
    )
