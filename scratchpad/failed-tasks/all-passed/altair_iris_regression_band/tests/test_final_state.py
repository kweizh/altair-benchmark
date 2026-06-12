import json
import os
import shutil
import subprocess

import pytest
from pochi_verifier import PochiVerifier

PROJECT_DIR = "/home/user/iris_chart"
CHART_PY = os.path.join(PROJECT_DIR, "chart.py")
CHART_JSON = os.path.join(PROJECT_DIR, "chart.json")
CHART_HTML = os.path.join(PROJECT_DIR, "chart.html")
LOG_FILE = os.path.join(PROJECT_DIR, "output.log")


def _cleanup_artifact(path: str) -> None:
    if os.path.isfile(path):
        os.remove(path)


@pytest.fixture(scope="session")
def chart_spec():
    """Run the agent's chart.py from a clean state and return the parsed Vega-Lite spec."""
    assert os.path.isfile(CHART_PY), f"Expected agent script at {CHART_PY}."

    _cleanup_artifact(CHART_JSON)
    _cleanup_artifact(CHART_HTML)
    _cleanup_artifact(LOG_FILE)

    python_bin = shutil.which("python") or shutil.which("python3")
    assert python_bin is not None, "No python interpreter available on PATH."

    result = subprocess.run(
        [python_bin, "chart.py"],
        capture_output=True,
        text=True,
        cwd=PROJECT_DIR,
        timeout=300,
    )
    assert result.returncode == 0, (
        f"'python chart.py' failed with code {result.returncode}.\n"
        f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
    )

    assert os.path.isfile(CHART_JSON), (
        f"Expected Vega-Lite spec at {CHART_JSON} after running chart.py."
    )
    with open(CHART_JSON, "r", encoding="utf-8") as f:
        spec = json.load(f)
    return spec


def _iter_layers(spec):
    """Yield every layer dict in a (possibly nested) Vega-Lite spec."""
    if not isinstance(spec, dict):
        return
    if "layer" in spec and isinstance(spec["layer"], list):
        for layer in spec["layer"]:
            yield layer
            yield from _iter_layers(layer)


def _mark_type(layer):
    mark = layer.get("mark") if isinstance(layer, dict) else None
    if isinstance(mark, str):
        return mark
    if isinstance(mark, dict):
        return mark.get("type")
    return None


def _mark_dict(layer):
    mark = layer.get("mark") if isinstance(layer, dict) else None
    if isinstance(mark, dict):
        return mark
    return {}


def test_required_artifacts_exist(chart_spec):
    assert os.path.isfile(CHART_PY), f"chart.py missing at {CHART_PY}."
    assert os.path.isfile(CHART_JSON), f"chart.json missing at {CHART_JSON}."
    assert os.path.isfile(CHART_HTML), f"chart.html missing at {CHART_HTML}."
    assert os.path.isfile(LOG_FILE), f"output.log missing at {LOG_FILE}."

    with open(LOG_FILE, "r", encoding="utf-8") as f:
        log_text = f.read()
    assert "Chart saved: /home/user/iris_chart/chart.html" in log_text, (
        f"Expected log line 'Chart saved: /home/user/iris_chart/chart.html' in {LOG_FILE}, "
        f"got: {log_text!r}"
    )


def test_top_level_is_layered_with_at_least_four_layers(chart_spec):
    assert isinstance(chart_spec, dict), "Vega-Lite spec must be a JSON object."
    layers = chart_spec.get("layer")
    assert isinstance(layers, list), (
        "Top-level spec must be a layered chart with a 'layer' array."
    )
    assert len(layers) >= 4, (
        f"Expected at least 4 layers (points, regression, loess, errorband); got {len(layers)}."
    )


def test_regression_transform_groupby_species(chart_spec):
    matches = []
    for layer in _iter_layers(chart_spec):
        transforms = layer.get("transform") if isinstance(layer, dict) else None
        if not isinstance(transforms, list):
            continue
        for t in transforms:
            if not isinstance(t, dict):
                continue
            if "regression" in t and "species" in (t.get("groupby") or []):
                matches.append(t)
    assert len(matches) >= 1, (
        "Expected at least one layer with a transform_regression that groups by 'species'."
    )
    t = matches[0]
    assert t.get("on") in {"petalLength", "petalWidth"}, (
        f"Regression transform 'on' field should reference petalLength/petalWidth, got: {t.get('on')!r}."
    )
    assert t.get("regression") in {"petalLength", "petalWidth"}, (
        f"Regression transform 'regression' field should reference petalLength/petalWidth, "
        f"got: {t.get('regression')!r}."
    )


def test_loess_transform_groupby_species_bandwidth_0_6(chart_spec):
    matches = []
    for layer in _iter_layers(chart_spec):
        transforms = layer.get("transform") if isinstance(layer, dict) else None
        if not isinstance(transforms, list):
            continue
        for t in transforms:
            if not isinstance(t, dict):
                continue
            if "loess" in t and "species" in (t.get("groupby") or []):
                matches.append(t)
    assert len(matches) >= 1, (
        "Expected at least one layer with a transform_loess that groups by 'species'."
    )
    t = matches[0]
    assert t.get("loess") == "petalWidth", (
        f"LOESS transform should smooth 'petalWidth', got: {t.get('loess')!r}."
    )
    assert t.get("on") == "petalLength", (
        f"LOESS transform 'on' should be 'petalLength', got: {t.get('on')!r}."
    )
    assert t.get("bandwidth") == 0.6, (
        f"LOESS bandwidth must be 0.6, got: {t.get('bandwidth')!r}."
    )


def test_errorband_layer_with_ci_or_stderr(chart_spec):
    band_layers = [
        layer for layer in _iter_layers(chart_spec) if _mark_type(layer) == "errorband"
    ]
    assert band_layers, (
        "Expected at least one layer with mark type 'errorband' for the confidence band."
    )
    extent_values = []
    for layer in band_layers:
        mark = _mark_dict(layer)
        extent = mark.get("extent")
        if extent is None:
            encoding = layer.get("encoding") if isinstance(layer, dict) else None
            if isinstance(encoding, dict):
                y = encoding.get("y")
                if isinstance(y, dict):
                    extent = y.get("extent")
        extent_values.append(extent)
    assert any(e in {"ci", "stderr"} for e in extent_values), (
        f"At least one errorband layer must use extent='ci' or 'stderr'; saw {extent_values!r}."
    )


def test_mark_coverage_point_line_errorband(chart_spec):
    mark_types = {
        _mark_type(layer) for layer in _iter_layers(chart_spec) if _mark_type(layer)
    }
    required = {"point", "line", "errorband"}
    missing = required - mark_types
    assert not missing, (
        f"Layered chart must include marks {sorted(required)}; missing: {sorted(missing)} "
        f"(saw: {sorted(mark_types)})."
    )


def test_loess_line_layer_has_stroke_dash(chart_spec):
    dashed_line_layers = []
    for layer in _iter_layers(chart_spec):
        if _mark_type(layer) != "line":
            continue
        mark = _mark_dict(layer)
        stroke_dash = mark.get("strokeDash")
        if isinstance(stroke_dash, list) and len(stroke_dash) >= 2 and all(
            isinstance(x, (int, float)) for x in stroke_dash
        ):
            dashed_line_layers.append(layer)
    assert dashed_line_layers, (
        "Expected at least one 'line' mark with a non-empty numeric strokeDash array "
        "(the LOESS layer should be rendered as a dashed line)."
    )


def test_title_is_structured_with_subtitle(chart_spec):
    title = chart_spec.get("title")
    assert isinstance(title, dict), (
        f"Top-level 'title' must be a structured object with 'text' and 'subtitle'; got: {type(title).__name__}."
    )
    text = title.get("text")
    assert isinstance(text, str) and text.strip(), (
        f"Title 'text' must be a non-empty string; got: {text!r}."
    )
    subtitle = title.get("subtitle")
    assert isinstance(subtitle, list), (
        f"Title 'subtitle' must be a list of strings (multi-line); got: {type(subtitle).__name__}."
    )
    assert len(subtitle) >= 2, (
        f"Title 'subtitle' must contain at least 2 lines; got {len(subtitle)} entries."
    )
    assert all(isinstance(line, str) and line.strip() for line in subtitle), (
        f"Every subtitle entry must be a non-empty string; got: {subtitle!r}."
    )


def test_browser_renders_layered_marks(chart_spec):
    assert os.path.isfile(CHART_HTML), (
        f"chart.html missing at {CHART_HTML}; cannot run browser verification."
    )

    reason = (
        "The HTML page at file:///home/user/iris_chart/chart.html must render a single "
        "layered Altair chart of the iris dataset showing four visual elements: a scatter "
        "of points colored by species, a solid regression line per species, a dashed LOESS "
        "smoothed line per species, and a translucent confidence band per species."
    )
    truth = (
        "Open file:///home/user/iris_chart/chart.html in the browser and wait for "
        "Vega-Embed to finish rendering. Verify the rendered chart contains: "
        "(1) multiple scatter point marks; "
        "(2) at least one solid line per species (the linear regression); "
        "(3) at least one dashed line per species (the LOESS smoother) with a visible dash pattern; "
        "(4) at least one filled translucent band region per species (the confidence band). "
        "Also verify the chart shows a title with a multi-line subtitle."
    )

    verifier = PochiVerifier()
    result = verifier.verify(
        reason=reason,
        truth=truth,
        use_browser_agent=True,
        trajectory_dir="/logs/verifier/pochi/test_browser_renders_layered_marks",
    )
    assert result.status == "pass", f"Browser verification failed: {result.reason}"
