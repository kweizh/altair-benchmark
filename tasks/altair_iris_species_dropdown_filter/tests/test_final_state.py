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

EXPECTED_OPTIONS = ["setosa", "versicolor", "virginica"]
EXPECTED_NAME = "Species: "


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


def _spec_mark_type(spec: dict[str, Any]) -> str:
    mark = spec.get("mark")
    if isinstance(mark, str):
        return mark
    if isinstance(mark, dict):
        return str(mark.get("type", ""))
    return ""


def _flatten_branches(condition: Any) -> list[dict[str, Any]]:
    """Vega-Lite color.condition may be a dict or a list of dicts (multiple conditions)."""
    if condition is None:
        return []
    if isinstance(condition, list):
        return [c for c in condition if isinstance(c, dict)]
    if isinstance(condition, dict):
        return [condition]
    return []


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


def test_spec_uses_point_or_circle_mark(vega_spec):
    mark_type = _spec_mark_type(vega_spec)
    assert mark_type in ("point", "circle"), (
        f"Expected the top-level mark to be `point` or `circle`, got `{mark_type}`."
    )


def test_x_and_y_encodings(vega_spec):
    encoding = vega_spec.get("encoding") or {}
    x = encoding.get("x") or {}
    y = encoding.get("y") or {}
    assert x.get("field") == "sepalLength", (
        f"Expected encoding.x.field == 'sepalLength', got {x.get('field')!r}."
    )
    assert y.get("field") == "sepalWidth", (
        f"Expected encoding.y.field == 'sepalWidth', got {y.get('field')!r}."
    )


def test_dropdown_param_present(vega_spec):
    params = vega_spec.get("params") or []
    assert isinstance(params, list) and len(params) >= 1, (
        "Expected the spec to declare at least one entry in `params`."
    )
    matching = []
    for p in params:
        if not isinstance(p, dict):
            continue
        bind = p.get("bind")
        if not isinstance(bind, dict):
            continue
        if bind.get("input") != "select":
            continue
        if bind.get("options") != EXPECTED_OPTIONS:
            continue
        if bind.get("name") != EXPECTED_NAME:
            continue
        matching.append(p)
    assert len(matching) == 1, (
        f"Expected exactly one params entry with bind.input == 'select', "
        f"bind.options == {EXPECTED_OPTIONS!r}, and bind.name == {EXPECTED_NAME!r}. "
        f"Got {len(matching)} matching entries out of {len(params)} params."
    )


def _find_species_dropdown_param_name(spec: dict[str, Any]) -> str:
    for p in spec.get("params") or []:
        if not isinstance(p, dict):
            continue
        bind = p.get("bind")
        if not isinstance(bind, dict):
            continue
        if (
            bind.get("input") == "select"
            and bind.get("options") == EXPECTED_OPTIONS
            and bind.get("name") == EXPECTED_NAME
        ):
            name = p.get("name")
            assert isinstance(name, str) and name, (
                "Bound species-dropdown parameter must have a string `name`."
            )
            return name
    raise AssertionError("Could not locate the bound species dropdown parameter.")


def test_color_encoding_is_conditional_on_param(vega_spec):
    param_name = _find_species_dropdown_param_name(vega_spec)
    encoding = vega_spec.get("encoding") or {}
    color = encoding.get("color")
    assert isinstance(color, dict), (
        f"Expected encoding.color to be a conditional object, got {type(color).__name__}."
    )

    # Identify default ("otherwise") branch yielding "lightgray", and the species branch.
    default_value = color.get("value")
    branches = _flatten_branches(color.get("condition"))
    assert branches, (
        "Expected encoding.color.condition to be a dict or list describing the conditional branches."
    )

    if default_value == "lightgray":
        # The species branch must reference `species` (nominal).
        species_branches = branches
    else:
        # Alternative representation: condition.value == 'lightgray', other side carries species color.
        species_branches = [b for b in branches if b.get("value") != "lightgray"]
        lightgray_branches = [b for b in branches if b.get("value") == "lightgray"]
        assert lightgray_branches, (
            "Expected one branch of encoding.color (either the default `value` or a `condition.value`) "
            "to resolve to the literal `'lightgray'`."
        )

    # At least one branch must reference the `species` nominal field.
    species_field_referenced = any(
        (b.get("field") == "species" and (b.get("type") == "nominal" or b.get("type") == "N"))
        for b in species_branches
    )
    assert species_field_referenced, (
        "Expected the non-lightgray branch of encoding.color to reference "
        "the `species` nominal field."
    )

    # The conditional must reference the bound param (either via condition.test or condition.param).
    def references_param(branch: dict[str, Any]) -> bool:
        test_expr = branch.get("test")
        if isinstance(test_expr, str) and param_name in test_expr:
            return True
        if isinstance(test_expr, dict):
            # nested predicate form
            if param_name in json.dumps(test_expr):
                return True
        if branch.get("param") == param_name:
            return True
        return False

    assert any(references_param(b) for b in branches), (
        f"Expected one of encoding.color.condition branches to reference the bound parameter "
        f"`{param_name}` via a `test` Vega expression or a `param` selection."
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


def test_browser_dropdown_highlights_species(chart_preview_server):
    reason = (
        "The Altair-generated chart.html must render an iris scatter plot of sepalLength vs sepalWidth "
        "alongside a bound 'Species: ' dropdown. Selecting a species in the dropdown must keep that "
        "species' points colored normally while turning all other species' points 'lightgray'."
    )
    truth = (
        f"Navigate to {chart_preview_server} in a browser. "
        "Wait for the Vega-Lite chart to finish rendering. "
        "Verify there are NO JavaScript console errors. "
        "Verify that the page contains a labelled dropdown with the visible label 'Species: ' and "
        "exactly three options: 'setosa', 'versicolor', 'virginica'. "
        "Verify that a scatter plot of points is rendered (sepalLength on the x axis, sepalWidth on the y axis). "
        "Inspect the rendered point colors: with the current default selection, the points belonging to the "
        "selected species should appear in a distinct (non-gray) color while the points for the other two "
        "species should be rendered in 'lightgray'. "
        "Then change the dropdown selection to 'virginica'. After the change, only the 'virginica' points "
        "should be colored, and the 'setosa' and 'versicolor' points should all turn 'lightgray'. "
        "Finally change the dropdown selection to 'versicolor' and verify the same behavior: only "
        "'versicolor' points keep their color and the rest become 'lightgray'."
    )
    verifier = PochiVerifier()
    result = verifier.verify(
        reason=reason,
        truth=truth,
        use_browser_agent=True,
        trajectory_dir="/logs/verifier/pochi/test_browser_dropdown_highlights_species",
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
