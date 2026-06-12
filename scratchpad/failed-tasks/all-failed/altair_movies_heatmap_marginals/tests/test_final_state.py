import json
import os
import socket

import pytest
from xprocess import ProcessStarter

PROJECT_DIR = "/home/user/myproject"
CHART_HTML = os.path.join(PROJECT_DIR, "chart.html")
HTTP_PORT = 8765


def _extract_spec(html: str) -> dict:
    """Extract the embedded Vega-Lite JSON spec from an Altair-generated HTML file."""
    marker = "var spec = "
    idx = html.find(marker)
    assert idx != -1, (
        "Could not find embedded Vega-Lite spec in chart.html (no 'var spec = ' marker)."
    )
    start = idx + len(marker)
    depth = 0
    in_string = False
    escape = False
    for i in range(start, len(html)):
        c = html[i]
        if escape:
            escape = False
            continue
        if c == "\\":
            escape = True
            continue
        if c == '"':
            in_string = not in_string
            continue
        if in_string:
            continue
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                return json.loads(html[start : i + 1])
    raise AssertionError(
        "Could not parse embedded Vega-Lite spec from chart.html (unbalanced braces)."
    )


def _iter_all_specs(node):
    if not isinstance(node, dict):
        return
    yield node
    for key in ("vconcat", "hconcat", "concat", "layer"):
        for child in node.get(key) or []:
            yield from _iter_all_specs(child)
    if isinstance(node.get("spec"), dict):
        yield from _iter_all_specs(node["spec"])


def _enc(node, channel):
    return (node.get("encoding") or {}).get(channel) or {}


def _mark_type(node):
    mark = node.get("mark")
    if isinstance(mark, str):
        return mark
    if isinstance(mark, dict):
        return mark.get("type")
    return None


def _find_params(spec):
    out = []
    for node in _iter_all_specs(spec):
        for p in node.get("params") or []:
            out.append(p)
    return out


def _brush_names(spec):
    names = []
    for p in _find_params(spec):
        sel = p.get("select")
        if isinstance(sel, dict) and sel.get("type") == "interval":
            names.append(p.get("name"))
    return names


def _has_filter_referencing(node, param_names):
    for t in node.get("transform") or []:
        f = t.get("filter")
        if isinstance(f, dict) and f.get("param") in param_names:
            return True
        if isinstance(f, str):
            for n in param_names:
                if n and n in f:
                    return True
    return False


def _get_subplots(spec):
    outer = spec.get("vconcat") or spec.get("concat")
    assert outer and isinstance(outer, list) and len(outer) >= 2, (
        "Top-level spec must be a vertical concatenation with at least two children "
        "(top marginal and heatmap-row)."
    )
    top, row = outer[0], outer[1]
    inner = row.get("hconcat") or row.get("concat")
    assert inner and isinstance(inner, list) and len(inner) >= 2, (
        "Second child of top-level concat must be a horizontal concatenation containing "
        "the heatmap (left) and the right marginal."
    )
    center, right = inner[0], inner[1]
    return top, center, right


@pytest.fixture(scope="session")
def spec():
    assert os.path.isfile(CHART_HTML), (
        f"Expected generated chart at {CHART_HTML}, but the file does not exist."
    )
    with open(CHART_HTML, "r", encoding="utf-8") as f:
        html = f.read()
    return _extract_spec(html)


@pytest.fixture(scope="session")
def http_server(xprocess):
    class Starter(ProcessStarter):
        name = "altair_static_server"
        args = ["python3", "-m", "http.server", str(HTTP_PORT), "--bind", "127.0.0.1"]
        env = os.environ.copy()
        popen_kwargs = {"cwd": PROJECT_DIR, "text": True}
        timeout = 60
        terminate_on_interrupt = True

        def startup_check(self):
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                return s.connect_ex(("127.0.0.1", HTTP_PORT)) == 0

    xprocess.ensure(Starter.name, Starter)
    yield f"http://127.0.0.1:{HTTP_PORT}/chart.html"
    info = xprocess.getinfo(Starter.name)
    info.terminate()


def test_chart_html_exists():
    assert os.path.isfile(CHART_HTML), (
        f"chart.html must be generated at {CHART_HTML} after running build_chart.py."
    )


def test_spec_is_nonempty(spec):
    assert isinstance(spec, dict) and spec, "Embedded Vega-Lite spec is empty or invalid."


def test_compound_layout_top_above_center_and_right(spec):
    outer_key = "vconcat" if "vconcat" in spec else ("concat" if "concat" in spec else None)
    assert outer_key in ("vconcat", "concat"), (
        f"Top-level spec must be a vertical concatenation; got top-level keys: {list(spec.keys())}."
    )
    outer = spec[outer_key]
    assert isinstance(outer, list) and len(outer) >= 2, (
        f"Top-level {outer_key} must have at least 2 children (top marginal and heatmap row)."
    )
    top, row = outer[0], outer[1]
    assert isinstance(top, dict), (
        "First child of the top-level concat must be a chart spec (top marginal histogram)."
    )
    inner_key = "hconcat" if "hconcat" in row else ("concat" if "concat" in row else None)
    assert inner_key in ("hconcat", "concat"), (
        f"Second child of the top-level concat must be a horizontal concatenation "
        f"(heatmap + right marginal); got keys: {list(row.keys())}."
    )
    inner = row[inner_key]
    assert isinstance(inner, list) and len(inner) >= 2, (
        "Heatmap row must contain at least 2 children (heatmap and right marginal)."
    )


def test_heatmap_is_rect_with_binned_x_and_y(spec):
    _top, center, _right = _get_subplots(spec)
    heatmap_candidates = [
        s for s in _iter_all_specs(center) if _mark_type(s) == "rect"
    ]
    assert heatmap_candidates, (
        "Center subplot must contain a rect mark (the heatmap)."
    )
    hm = heatmap_candidates[0]
    x = _enc(hm, "x")
    y = _enc(hm, "y")
    assert x.get("field") == "IMDB_Rating", (
        f"Heatmap x channel must encode 'IMDB_Rating'; got {x.get('field')!r}."
    )
    assert y.get("field") == "Rotten_Tomatoes_Rating", (
        f"Heatmap y channel must encode 'Rotten_Tomatoes_Rating'; got {y.get('field')!r}."
    )
    for ch_name, ch in (("x", x), ("y", y)):
        bin_val = ch.get("bin")
        assert bin_val, (
            f"Heatmap {ch_name} channel must have bin enabled (got {bin_val!r})."
        )
        if isinstance(bin_val, dict):
            maxbins = bin_val.get("maxbins")
            assert maxbins is not None and 15 <= int(maxbins) <= 25, (
                f"Heatmap {ch_name} bin must declare maxbins ~ 20; got maxbins={maxbins!r}."
            )


def test_heatmap_color_uses_count_aggregate_with_viridis(spec):
    _top, center, _right = _get_subplots(spec)
    hm = next((s for s in _iter_all_specs(center) if _mark_type(s) == "rect"), None)
    assert hm is not None, "Heatmap rect mark not found in center subplot."
    color = _enc(hm, "color")
    assert color.get("aggregate") == "count", (
        f"Heatmap color encoding must use the count() aggregate; got aggregate={color.get('aggregate')!r}."
    )
    scale = color.get("scale") or {}
    assert scale.get("scheme") == "viridis", (
        f"Heatmap color scale must use the 'viridis' scheme; got scheme={scale.get('scheme')!r}."
    )


def test_2d_interval_brush_on_heatmap(spec):
    params = _find_params(spec)
    interval_params = []
    for p in params:
        sel = p.get("select")
        if isinstance(sel, dict) and sel.get("type") == "interval":
            interval_params.append(p)
    assert interval_params, (
        "Spec must declare at least one interval-selection parameter (the 2D brush)."
    )
    xy_brushes = []
    for p in interval_params:
        sel = p.get("select")
        encs = (sel or {}).get("encodings") or []
        if "x" in encs and "y" in encs:
            xy_brushes.append(p["name"])
    assert xy_brushes, (
        "An interval selection projected over BOTH 'x' and 'y' encodings is required "
        f"(2D brush). Found interval params: {[p.get('name') for p in interval_params]}."
    )

    _top, center, _right = _get_subplots(spec)
    heatmap_param_names = []
    for node in _iter_all_specs(center):
        for p in node.get("params") or []:
            heatmap_param_names.append(p.get("name"))
    assert any(n in xy_brushes for n in heatmap_param_names), (
        "The 2D-brush interval selection must be attached to the heatmap subplot. "
        f"Heatmap params: {heatmap_param_names}; 2D-brush params: {xy_brushes}."
    )


def _check_layered_marginal(marginal: dict, brush_names: list[str], axis: str):
    layers = marginal.get("layer")
    assert isinstance(layers, list) and len(layers) >= 2, (
        f"{axis} marginal must be a layered chart with at least 2 bar layers "
        f"(gray total + colored filtered)."
    )
    bar_layers = [l for l in layers if _mark_type(l) == "bar"]
    assert len(bar_layers) >= 2, (
        f"{axis} marginal must contain at least 2 bar layers; found {len(bar_layers)}."
    )
    filtered = [l for l in layers if _has_filter_referencing(l, brush_names)]
    assert filtered, (
        f"{axis} marginal must include a layer whose transform_filter references the brush "
        f"parameter (one of {brush_names})."
    )


def test_top_marginal_is_layered_with_brush_filter(spec):
    top, _center, _right = _get_subplots(spec)
    brush_names = _brush_names(spec)
    assert brush_names, "Spec must include at least one interval-selection parameter."
    _check_layered_marginal(top, brush_names, "Top")


def test_right_marginal_is_layered_with_brush_filter(spec):
    _top, _center, right = _get_subplots(spec)
    brush_names = _brush_names(spec)
    assert brush_names, "Spec must include at least one interval-selection parameter."
    _check_layered_marginal(right, brush_names, "Right")


def test_browser_renders_three_subplots(http_server):
    from pochi_verifier import PochiVerifier  # type: ignore

    reason = (
        "The generated dashboard must render three visible subplots arranged as a top marginal "
        "histogram, a center 2D heatmap, and a right marginal histogram (with horizontal bars). "
        "The heatmap area must visibly contain a grid of colored rectangles colored by count."
    )
    truth = (
        f"Open {http_server} in the browser. Verify that the page renders three subplots: "
        "(1) a bar histogram across the top, (2) a rectangular heatmap in the center that "
        "visibly contains a grid of colored rectangles, and (3) a horizontal-bar histogram on "
        "the right. All three subplots must be visible at the same time, with the top histogram "
        "aligned above the heatmap and the right histogram aligned to the right of the heatmap."
    )

    verifier = PochiVerifier()
    result = verifier.verify(
        reason=reason,
        truth=truth,
        use_browser_agent=True,
        trajectory_dir="/logs/verifier/pochi/test_browser_renders_three_subplots",
    )
    assert getattr(result, "status", None) == "pass", (
        f"Browser verification failed: {getattr(result, 'reason', result)!r}"
    )
