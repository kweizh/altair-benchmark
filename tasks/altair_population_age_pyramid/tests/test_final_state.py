import json
import os
import re
import subprocess

import pytest
from pochi_verifier import PochiVerifier

PROJECT_DIR = "/home/user/myproject"
HTML_PATH = os.path.join(PROJECT_DIR, "pyramid.html")
SPEC_PATH = os.path.join(PROJECT_DIR, "pyramid_spec.json")
DATASET_URL = "https://vega.github.io/vega-datasets/data/population.json"


# ---------------------------------------------------------------------------
# Setup: run the build script once for this test session.
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session", autouse=True)
def _run_build_script():
    # Clean up any previous outputs so we test a fresh run.
    for path in (HTML_PATH, SPEC_PATH):
        if os.path.exists(path):
            os.remove(path)

    result = subprocess.run(
        ["python", "build_pyramid.py"],
        cwd=PROJECT_DIR,
        capture_output=True,
        text=True,
        timeout=180,
    )
    assert result.returncode == 0, (
        "build_pyramid.py failed to run.\n"
        f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
    )
    yield


@pytest.fixture(scope="session")
def spec() -> dict:
    assert os.path.isfile(SPEC_PATH), (
        f"Vega-Lite spec file {SPEC_PATH} was not produced by build_pyramid.py."
    )
    with open(SPEC_PATH) as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# Helpers to walk the spec.
# ---------------------------------------------------------------------------


def _iter_nodes(obj):
    """Yield every dict/list node nested inside obj (including obj itself)."""
    yield obj
    if isinstance(obj, dict):
        for v in obj.values():
            yield from _iter_nodes(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from _iter_nodes(v)


def _all_transforms(spec: dict) -> list[dict]:
    """Return every transform entry from every `transform` list found in the spec."""
    out: list[dict] = []
    for node in _iter_nodes(spec):
        if isinstance(node, dict) and isinstance(node.get("transform"), list):
            for t in node["transform"]:
                if isinstance(t, dict):
                    out.append(t)
    return out


def _all_encodings(spec: dict) -> list[dict]:
    out: list[dict] = []
    for node in _iter_nodes(spec):
        if isinstance(node, dict) and isinstance(node.get("encoding"), dict):
            out.append(node["encoding"])
    return out


def _all_marks(spec: dict) -> list:
    out: list = []
    for node in _iter_nodes(spec):
        if isinstance(node, dict) and "mark" in node:
            out.append(node["mark"])
    return out


def _all_data_urls(spec: dict) -> list[str]:
    urls: list[str] = []
    for node in _iter_nodes(spec):
        if isinstance(node, dict):
            data = node.get("data")
            if isinstance(data, dict) and isinstance(data.get("url"), str):
                urls.append(data["url"])
    return urls


def _all_params(spec: dict) -> list[dict]:
    out: list[dict] = []
    for node in _iter_nodes(spec):
        if isinstance(node, dict) and isinstance(node.get("params"), list):
            for p in node["params"]:
                if isinstance(p, dict):
                    out.append(p)
    return out


# ---------------------------------------------------------------------------
# Artifact existence.
# ---------------------------------------------------------------------------


def test_html_artifact_exists():
    assert os.path.isfile(HTML_PATH), f"Expected HTML artifact at {HTML_PATH}."
    assert os.path.getsize(HTML_PATH) > 0, f"{HTML_PATH} is empty."
    with open(HTML_PATH) as f:
        html = f.read()
    assert "<script" in html.lower(), (
        f"{HTML_PATH} does not contain a <script> tag; it does not look like an Altair-generated HTML."
    )


def test_spec_artifact_exists(spec: dict):
    assert isinstance(spec, dict) and spec, (
        f"{SPEC_PATH} did not deserialize to a non-empty dict."
    )


# ---------------------------------------------------------------------------
# Spec structure.
# ---------------------------------------------------------------------------


def test_population_dataset_url(spec: dict):
    urls = _all_data_urls(spec)
    assert DATASET_URL in urls, (
        f"Spec must reference the dataset URL {DATASET_URL!r}. Found data URLs: {urls!r}."
    )


def test_calculate_transform_signs_people_by_sex(spec: dict):
    """A `calculate` transform must turn `people` into a signed value based on `sex`."""
    transforms = _all_transforms(spec)
    calc_transforms = [t for t in transforms if "calculate" in t and "as" in t]
    assert calc_transforms, (
        "No `calculate` transform found. A `transform_calculate` is required to build the signed "
        "people field."
    )

    pattern = re.compile(
        r"datum\.sex\s*===?\s*1.*-\s*datum\.people.*datum\.people",
        re.DOTALL,
    )
    alt_pattern = re.compile(
        r"if\s*\(\s*datum\.sex\s*===?\s*1\s*,\s*-\s*datum\.people\s*,\s*datum\.people\s*\)",
        re.DOTALL,
    )

    matching = [
        t
        for t in calc_transforms
        if pattern.search(t["calculate"]) or alt_pattern.search(t["calculate"])
    ]
    assert matching, (
        "Did not find a `calculate` transform expressing the signed-people calculation. "
        "Expected an expression equivalent to `datum.sex == 1 ? -datum.people : datum.people` "
        f"or `if(datum.sex === 1, -datum.people, datum.people)`. Got calculates: "
        f"{[t['calculate'] for t in calc_transforms]!r}."
    )


def test_filter_transform_references_year_param(spec: dict):
    """A `filter` transform must filter by the year-selection parameter."""
    transforms = _all_transforms(spec)
    filter_transforms = [t for t in transforms if "filter" in t]
    assert filter_transforms, (
        "No `filter` transform found. A `transform_filter` is required to restrict the chart to "
        "the year selected via the dropdown."
    )

    params = _all_params(spec)
    param_names = {p.get("name") for p in params if isinstance(p.get("name"), str)}

    def references_year(filt_value) -> bool:
        if isinstance(filt_value, dict):
            param_ref = filt_value.get("param")
            if isinstance(param_ref, str) and (param_ref in param_names or "year" in param_ref.lower()):
                return True
            # Some specs wrap the param reference under a different key; serialize and inspect.
            return "year" in json.dumps(filt_value).lower()
        if isinstance(filt_value, str):
            text = filt_value.lower()
            return "year" in text and ("datum" in text or "param" in text or any(name.lower() in text for name in param_names))
        return False

    assert any(references_year(t["filter"]) for t in filter_transforms), (
        "The `transform_filter` does not reference the year parameter / `datum.year`. "
        f"Got filter entries: {[t['filter'] for t in filter_transforms]!r}."
    )


def test_mark_is_bar(spec: dict):
    marks = _all_marks(spec)
    normalized = []
    for m in marks:
        if isinstance(m, str):
            normalized.append(m)
        elif isinstance(m, dict):
            normalized.append(m.get("type"))
    assert "bar" in normalized, (
        f"Expected the chart's `mark` to be `bar`. Found marks: {marks!r}."
    )


# ---------------------------------------------------------------------------
# Encoding checks.
# ---------------------------------------------------------------------------


def _get_encoding(spec: dict, channel: str) -> dict:
    for enc in _all_encodings(spec):
        if isinstance(enc.get(channel), dict):
            return enc[channel]
    raise AssertionError(f"No `encoding.{channel}` found in the spec.")


def test_x_encoding_uses_signed_field_with_abs_label_expr(spec: dict):
    x = _get_encoding(spec, "x")
    assert x.get("type") == "quantitative", (
        f"x encoding must be quantitative, got {x.get('type')!r}."
    )

    # Identify the calculated signed field via the `as` of the calculate transform,
    # then ensure the x encoding's field equals it.
    calc_transforms = [
        t for t in _all_transforms(spec) if "calculate" in t and "as" in t
    ]
    signed_fields = {t["as"] for t in calc_transforms}
    assert x.get("field") in signed_fields, (
        f"x encoding's field {x.get('field')!r} does not match the signed field produced "
        f"by transform_calculate (candidates: {signed_fields!r})."
    )

    axis = x.get("axis")
    assert isinstance(axis, dict), (
        "x encoding is missing an `axis` configuration; expected `format` and `labelExpr` keys."
    )
    assert "format" in axis, (
        "x.axis is missing `format` (expected a numeric format such as 's')."
    )
    label_expr = axis.get("labelExpr")
    assert isinstance(label_expr, str) and "abs(" in label_expr, (
        f"x.axis.labelExpr must use `abs(...)` to display absolute-value labels. Got: {label_expr!r}."
    )


def test_y_encoding_is_age_ordinal_reversed(spec: dict):
    y = _get_encoding(spec, "y")
    assert y.get("field") == "age", (
        f"y encoding must use the `age` field, got {y.get('field')!r}."
    )
    assert y.get("type") == "ordinal", (
        f"y encoding must be ordinal, got {y.get('type')!r}."
    )
    sort_value = y.get("sort")
    valid = False
    if isinstance(sort_value, str) and sort_value in {"descending", "-age"}:
        valid = True
    elif isinstance(sort_value, dict):
        if sort_value.get("order") == "descending" and sort_value.get("field") in {"age", None}:
            valid = True
    assert valid, (
        "y encoding must sort the `age` axis so the oldest age is at the top. "
        f"Expected sort to be 'descending', '-age', or an object with order='descending'. "
        f"Got: {sort_value!r}."
    )


def test_color_encoding_custom_scale_and_legend(spec: dict):
    color = _get_encoding(spec, "color")
    assert color.get("field") == "sex", (
        f"color encoding must use the `sex` field, got {color.get('field')!r}."
    )
    assert color.get("type") == "nominal", (
        f"color encoding must be nominal, got {color.get('type')!r}."
    )

    scale = color.get("scale")
    assert isinstance(scale, dict), "color encoding must include an explicit `scale`."
    assert scale.get("domain") == [1, 2], (
        f"color.scale.domain must be [1, 2] (Male, Female). Got: {scale.get('domain')!r}."
    )
    color_range = scale.get("range")
    assert isinstance(color_range, list) and len(color_range) == 2, (
        f"color.scale.range must be a list of exactly two colors. Got: {color_range!r}."
    )
    assert all(isinstance(c, str) and c for c in color_range), (
        f"color.scale.range entries must be non-empty color strings. Got: {color_range!r}."
    )

    legend = color.get("legend")
    assert isinstance(legend, dict), (
        "color encoding must include an explicit `legend` configuration with a labelExpr."
    )
    label_expr = legend.get("labelExpr")
    assert isinstance(label_expr, str), (
        f"color.legend.labelExpr must be a string Vega expression. Got: {label_expr!r}."
    )
    assert "Male" in label_expr and "Female" in label_expr, (
        "color.legend.labelExpr must produce the strings 'Male' and 'Female'. "
        f"Got: {label_expr!r}."
    )
    assert "datum.value" in label_expr, (
        f"color.legend.labelExpr should reference `datum.value`. Got: {label_expr!r}."
    )


# ---------------------------------------------------------------------------
# Year dropdown parameter.
# ---------------------------------------------------------------------------


def test_year_dropdown_param(spec: dict):
    params = _all_params(spec)
    select_params = []
    for p in params:
        bind = p.get("bind")
        select_block = p.get("select")
        # `bind` may be a dict directly (binding_select) or live on the `select` dict.
        bind_input = None
        if isinstance(bind, dict):
            bind_input = bind.get("input")
        elif isinstance(select_block, dict):
            inner_bind = select_block.get("bind")
            if isinstance(inner_bind, dict):
                bind_input = inner_bind.get("input")
        if bind_input == "select":
            select_params.append(p)

    assert len(select_params) == 1, (
        f"Expected exactly one parameter bound to a `binding_select`. Found {len(select_params)} "
        f"out of params: {params!r}."
    )

    param = select_params[0]
    bind_block = param.get("bind") if isinstance(param.get("bind"), dict) else None
    if bind_block is None and isinstance(param.get("select"), dict):
        bind_block = param["select"].get("bind")
    assert isinstance(bind_block, dict), (
        f"Could not locate a bind dict for the year-select parameter. Param: {param!r}."
    )
    options = bind_block.get("options")
    assert isinstance(options, list) and 1980 in options, (
        f"binding_select.options must include 1980. Got options: {options!r}."
    )

    # Initial value: either param.value == 1980, or select.init has year == 1980.
    initial_ok = False
    if param.get("value") == 1980:
        initial_ok = True
    select_block = param.get("select")
    if isinstance(select_block, dict):
        init = select_block.get("init")
        if isinstance(init, dict) and init.get("year") == 1980:
            initial_ok = True
        elif isinstance(init, list):
            for entry in init:
                if isinstance(entry, dict) and entry.get("year") == 1980:
                    initial_ok = True
                    break
    assert initial_ok, (
        "The year-select parameter must have an initial value of 1980 (either via `value: 1980` "
        f"or via `select.init`). Param: {param!r}."
    )


# ---------------------------------------------------------------------------
# Browser verification.
# ---------------------------------------------------------------------------


def test_browser_renders_pyramid_with_dropdown_and_signed_bars():
    verifier = PochiVerifier()
    reason = (
        "The Altair-generated HTML must render a back-to-back age pyramid with a year-select "
        "dropdown widget and bars extending in both directions (males to the left, females to the right)."
    )
    truth = (
        f"Open the local file file://{HTML_PATH} in a browser. "
        "Wait for the Vega-Embed view to finish rendering (the page should contain a `.vega-embed` "
        "container with an `<svg>` or `<canvas>` element). "
        "Verify the following: "
        "(1) The DOM contains at least one `<select>` element (the year dropdown produced by the binding_select). "
        "(2) The rendered chart shows at least one bar that extends to the LEFT of the chart's x=0 baseline "
        "(this is the negative `signed_people` for males) AND at least one bar that extends to the RIGHT of the "
        "x=0 baseline (positive `signed_people` for females). The simplest way is to inspect the SVG `rect` (or "
        "`path`) bar marks under the `.vega-embed > svg .mark-rect` group: their `x` attribute values must include "
        "both values smaller than the center of the plotting area and larger than the center. "
        "Do NOT change the dropdown selection; just verify the default render."
    )
    result = verifier.verify(
        reason=reason,
        truth=truth,
        use_browser_agent=True,
        trajectory_dir="/logs/verifier/pochi/test_browser_renders_pyramid_with_dropdown_and_signed_bars",
    )
    assert result.status == "pass", f"Browser verification failed: {result.reason}"
