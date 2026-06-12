import importlib
import os

PROJECT_DIR = "/home/user/myproject"
SOLUTION_PATH = os.path.join(PROJECT_DIR, "solution.py")


def test_altair_importable():
    """The target library `altair` must be installed and importable."""
    try:
        importlib.import_module("altair")
    except Exception as exc:  # pragma: no cover - failure path
        raise AssertionError(
            f"`altair` is not importable in the evaluation environment: {exc!r}"
        )


def test_vega_datasets_importable():
    """The cars dataset is sourced from `vega_datasets`; the package must be available."""
    try:
        importlib.import_module("vega_datasets")
    except Exception as exc:  # pragma: no cover - failure path
        raise AssertionError(
            f"`vega_datasets` is not importable in the evaluation environment: {exc!r}"
        )


def test_project_directory_exists():
    """The task's project directory must be present before the executor starts."""
    assert os.path.isdir(PROJECT_DIR), (
        f"Project directory {PROJECT_DIR} does not exist."
    )


def test_solution_stub_present():
    """A starter stub for the executor's entry-point file must already exist."""
    assert os.path.isfile(SOLUTION_PATH), (
        f"Expected starter stub at {SOLUTION_PATH}; it is missing."
    )


def test_chart_html_not_yet_produced():
    """The chart artifact must NOT be present at the initial state."""
    artifact = os.path.join(PROJECT_DIR, "chart.html")
    assert not os.path.exists(artifact), (
        f"chart.html should not exist before the executor runs solution.py, "
        f"but found {artifact}."
    )
