import json
import os
import re
import socket
import subprocess
from typing import Any

import pytest
from pochi_verifier import PochiVerifier
from xprocess import ProcessStarter


PROJECT_DIR = "/home/user/project"
BUILD_SCRIPT = os.path.join(PROJECT_DIR, "build_dashboard.py")
HTML_PATH = os.path.join(PROJECT_DIR, "movies_dashboard.html")
SERVER_PORT = 8765
SERVER_URL = f"http://localhost:{SERVER_PORT}/movies_dashboard.html"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _extract_spec_from_html(html_text: str) -> dict[str, Any]:
    """Extract the embedded Vega-Lite JSON spec from an Altair-generated HTML file.

    Altair's default HTML template defines the spec as a JS object literal that is
    passed to ``vegaEmbed(...)``. We locate the ``var spec = {`` assignment (or the
    ``vegaEmbed("#vis", {...}, ...)`` literal) and use brace counting to extract a
    balanced JSON object, then parse it with ``json.loads``.
    """

    candidates: list[int] = []

    # Pattern 1: ``var spec = { ... };``
    for match in re.finditer(r"var\s+spec\s*=\s*\{", html_text):
        candidates.append(match.end() - 1)

    # Pattern 2: ``vegaEmbed("#vis", { ... }, ...)``
    for match in re.finditer(r"vegaEmbed\s*\(\s*['\"][^'\"]+['\"]\s*,\s*\{", html_text):
        candidates.append(match.end() - 1)

    last_error: Exception | None = None
    for start in candidates:
        depth = 0
        in_string = False
        escape = False
        for i in range(start, len(html_text)):
            ch = html_text[i]
            if in_string:
                if escape:
                    escape = False
                elif ch == "\\":
                    escape = True
                elif ch == '"':
                    in_string = False
            else:
                if ch == '"':
                    in_string = True
                elif ch == "{":
                    depth += 1
                elif ch == "}":
                    depth -= 1
                    if depth == 0:
                        candidate = html_text[start : i + 1]
                        try:
                            return json.loads(candidate)
                        except json.JSONDecodeError as e:
                            last_error = e
                            break

    raise AssertionError(
        f"Could not extract a valid Vega-Lite JSON spec from the generated HTML. "
        f"Last JSON error: {last_error}"
    )


def _collect_transforms(spec: dict[str, Any]) -> list[dict[str, Any]]:
    """Return the list of transform entries from the top-level spec.

    Altair always serializes transforms as a top-level ``transform`` array when
    using a single chart, which is what this task requires.
    """

    transforms = spec.get("transform")
    assert isinstance(transforms, list), (
        "Expected the embedded spec to expose a top-level 'transform' list, "
        f"got {type(transforms).__name__}."
    )
    return transforms


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session", autouse=True)
def build_dashboard():
    """Run the executor's build script to (re)generate the HTML artifact."""

    if os.path.exists(HTML_PATH):
        os.remove(HTML_PATH)

    assert os.path.isfile(BUILD_SCRIPT), (
        f"Build script {BUILD_SCRIPT} does not exist; the executor must provide it."
    )

    result = subprocess.run(
        ["python3", BUILD_SCRIPT],
        capture_output=True,
        text=True,
        cwd=PROJECT_DIR,
    )
    assert result.returncode == 0, (
        f"Build script failed with exit code {result.returncode}. "
        f"stdout=\n{result.stdout}\nstderr=\n{result.stderr}"
    )
    yield


@pytest.fixture(scope="session")
def html_text(build_dashboard) -> str:
    assert os.path.isfile(HTML_PATH), (
        f"Expected dashboard HTML at {HTML_PATH} after running the build script, "
        "but it is missing."
    )
    with open(HTML_PATH, "r", encoding="utf-8") as f:
        return f.read()


@pytest.fixture(scope="session")
def vega_spec(html_text: str) -> dict[str, Any]:
    return _extract_spec_from_html(html_text)


@pytest.fixture(scope="session")
def static_server(build_dashboard, xprocess):
    """Serve the project directory over HTTP so the browser verifier can load the file."""

    class Starter(ProcessStarter):
        name = "altair_static_server"
        args = ["python3", "-m", "http.server", str(SERVER_PORT), "--bind", "127.0.0.1"]
        env = os.environ.copy()
        popen_kwargs = {
            "cwd": PROJECT_DIR,
            "text": True,
        }
        timeout = 60
        terminate_on_interrupt = True

        def startup_check(self):
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                return s.connect_ex(("127.0.0.1", SERVER_PORT)) == 0

    xprocess.ensure(Starter.name, Starter)
    yield SERVER_URL
    info = xprocess.getinfo(Starter.name)
    info.terminate()


@pytest.fixture(scope="session")
def browser_verifier() -> PochiVerifier:
    return PochiVerifier()


# ---------------------------------------------------------------------------
# Spec-level assertions
# ---------------------------------------------------------------------------


def test_html_artifact_exists(html_text: str):
    assert len(html_text.strip()) > 0, f"{HTML_PATH} is empty."
    assert "vegaEmbed" in html_text, (
        f"{HTML_PATH} does not contain a vegaEmbed call; it does not look like an "
        "Altair-generated HTML dashboard."
    )


def test_spec_uses_movies_url(vega_spec: dict[str, Any]):
    data = vega_spec.get("data")
    assert isinstance(data, dict), "Embedded spec is missing a top-level 'data' object."
    url = data.get("url", "")
    assert isinstance(url, str) and url.endswith("data/movies.json"), (
        "Expected the spec's data URL to point at the vega-datasets movies.json "
        f"file, but got: {url!r}"
    )


def test_spec_declares_two_params(vega_spec: dict[str, Any]):
    params = vega_spec.get("params")
    assert isinstance(params, list), "Expected top-level 'params' to be a list."
    assert len(params) == 2, (
        f"Expected exactly two top-level params (one select binding and one range "
        f"binding), got {len(params)}: {params!r}"
    )


def test_params_include_genre_select_with_all_option(vega_spec: dict[str, Any]):
    params = vega_spec.get("params", [])
    select_params = [
        p for p in params if isinstance(p.get("bind"), dict)
        and p["bind"].get("input") == "select"
    ]
    assert len(select_params) == 1, (
        f"Expected exactly one param with a 'select' binding, found {len(select_params)}."
    )
    select_param = select_params[0]
    options = select_param["bind"].get("options")
    assert isinstance(options, list), (
        f"Select binding is missing an 'options' list: {select_param['bind']!r}"
    )
    assert "All" in options, (
        f"Select binding options must include the string 'All' (to disable the genre "
        f"filter), but got: {options!r}"
    )
    assert isinstance(select_param.get("name"), str) and select_param["name"], (
        "Select param must have a non-empty 'name' so that the transform_filter can "
        "reference it."
    )


def test_params_include_year_range_slider(vega_spec: dict[str, Any]):
    params = vega_spec.get("params", [])
    range_params = [
        p for p in params if isinstance(p.get("bind"), dict)
        and p["bind"].get("input") == "range"
    ]
    assert len(range_params) == 1, (
        f"Expected exactly one param with a 'range' binding, found {len(range_params)}."
    )
    range_param = range_params[0]
    binding = range_param["bind"]
    assert binding.get("min") == 1980, (
        f"Range binding 'min' must be 1980, got {binding.get('min')!r}."
    )
    assert binding.get("max") == 2020, (
        f"Range binding 'max' must be 2020, got {binding.get('max')!r}."
    )
    assert binding.get("step") == 1, (
        f"Range binding 'step' must be 1, got {binding.get('step')!r}."
    )
    assert isinstance(range_param.get("name"), str) and range_param["name"], (
        "Range param must have a non-empty 'name' so the color condition can reference it."
    )


def test_transform_calculate_release_year(vega_spec: dict[str, Any]):
    transforms = _collect_transforms(vega_spec)
    calc_steps = [t for t in transforms if "calculate" in t]
    matching = [
        t for t in calc_steps
        if t.get("as") == "Release_Year"
        and "Release_Date" in str(t.get("calculate", ""))
    ]
    assert matching, (
        "Expected a transform_calculate that produces an 'as=\"Release_Year\"' field "
        f"derived from Release_Date. transforms={transforms!r}"
    )


def test_transform_filter_references_genre_param(vega_spec: dict[str, Any]):
    params = vega_spec.get("params", [])
    select_param = next(
        (p for p in params if isinstance(p.get("bind"), dict)
         and p["bind"].get("input") == "select"),
        None,
    )
    assert select_param is not None, "Could not find the genre select param."
    genre_name = select_param["name"]

    transforms = _collect_transforms(vega_spec)
    filter_steps = [t for t in transforms if "filter" in t]
    assert filter_steps, "Expected at least one transform_filter step in the spec."

    def _filter_text(step: dict[str, Any]) -> str:
        f = step["filter"]
        return f if isinstance(f, str) else json.dumps(f)

    matched = any(genre_name in _filter_text(step) for step in filter_steps)
    assert matched, (
        f"Expected a transform_filter whose predicate references the genre param "
        f"name {genre_name!r}, but no filter referenced it. filters={filter_steps!r}"
    )


def test_x_and_y_use_log_scales(vega_spec: dict[str, Any]):
    encoding = vega_spec.get("encoding")
    assert isinstance(encoding, dict), "Spec must include an 'encoding' object."

    x_scale = encoding.get("x", {}).get("scale", {})
    y_scale = encoding.get("y", {}).get("scale", {})
    assert x_scale.get("type") == "log", (
        f"x-axis must use a logarithmic scale (scale.type == 'log'), got {x_scale!r}."
    )
    assert y_scale.get("type") == "log", (
        f"y-axis must use a logarithmic scale (scale.type == 'log'), got {y_scale!r}."
    )

    x_field = encoding.get("x", {}).get("field")
    y_field = encoding.get("y", {}).get("field")
    assert x_field == "Production_Budget", (
        f"x encoding must use the 'Production_Budget' field, got {x_field!r}."
    )
    assert y_field == "Worldwide_Gross", (
        f"y encoding must use the 'Worldwide_Gross' field, got {y_field!r}."
    )


def test_color_condition_uses_year_param(vega_spec: dict[str, Any]):
    params = vega_spec.get("params", [])
    year_param = next(
        (p for p in params if isinstance(p.get("bind"), dict)
         and p["bind"].get("input") == "range"),
        None,
    )
    assert year_param is not None, "Could not find the year range param."
    year_name = year_param["name"]

    color = vega_spec.get("encoding", {}).get("color")
    assert isinstance(color, dict), "Color encoding must be a conditional encoding object."

    condition = color.get("condition")
    assert condition is not None, (
        f"Color encoding must include a 'condition' (e.g. via alt.when/alt.condition), "
        f"got {color!r}."
    )

    # ``condition`` may be a dict or a list of dicts; normalize.
    cond_entries = condition if isinstance(condition, list) else [condition]

    def _cond_text(entry: dict[str, Any]) -> str:
        for key in ("test", "param"):
            val = entry.get(key)
            if isinstance(val, str):
                return val
            if val is not None:
                return json.dumps(val)
        return json.dumps(entry)

    assert any(year_name in _cond_text(c) for c in cond_entries), (
        f"Color condition must reference the year param {year_name!r}, "
        f"got conditions={cond_entries!r}."
    )

    otherwise_value = color.get("value")
    assert otherwise_value == "lightgray", (
        "Color encoding's else-branch (alt.value(...)) must be the string 'lightgray', "
        f"got {otherwise_value!r}."
    )


def test_color_field_is_major_genre(vega_spec: dict[str, Any]):
    color = vega_spec.get("encoding", {}).get("color", {})
    condition = color.get("condition")
    assert condition is not None, "Color encoding must be conditional."
    entry = condition[0] if isinstance(condition, list) else condition
    assert entry.get("field") == "Major_Genre", (
        f"Color condition's 'then' branch must encode Major_Genre, got {entry!r}."
    )


# ---------------------------------------------------------------------------
# Browser verification
# ---------------------------------------------------------------------------


def test_browser_renders_widget_controls(static_server, browser_verifier):
    reason = (
        "The generated dashboard HTML must produce a working Vega-Embed view that "
        "exposes two bound widget controls: a dropdown for the Major_Genre filter and "
        "a range slider for the release year."
    )
    truth = (
        f"Navigate to {SERVER_URL}. Wait for vegaEmbed to finish rendering the chart. "
        "Verify that the page DOM contains at least one <select> element (the genre "
        "dropdown) and at least one <input type=\"range\"> element (the release-year "
        "slider). Also verify the chart itself rendered by confirming the page contains "
        "either a <canvas> or an <svg> element produced by the Vega view. Report a "
        "failure if any required element is missing or if the JavaScript console shows "
        "errors from vegaEmbed."
    )

    result = browser_verifier.verify(
        reason=reason,
        truth=truth,
        use_browser_agent=True,
        trajectory_dir="/logs/verifier/pochi/test_browser_renders_widget_controls",
    )
    assert result.status == "pass", (
        f"Browser verification failed: {getattr(result, 'reason', result)!r}"
    )
