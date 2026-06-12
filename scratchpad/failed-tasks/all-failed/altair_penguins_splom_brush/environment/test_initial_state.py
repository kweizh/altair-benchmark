import importlib
import os


PROJECT_DIR = "/home/user/myproject"
SOLUTION_FILE = os.path.join(PROJECT_DIR, "solution.py")


def test_altair_importable():
    try:
        importlib.import_module("altair")
    except ImportError as exc:  # pragma: no cover - asserted as failure below
        raise AssertionError(
            f"Expected the 'altair' library to be importable in the task environment: {exc}"
        )


def test_vega_datasets_importable():
    try:
        importlib.import_module("vega_datasets")
    except ImportError as exc:  # pragma: no cover - asserted as failure below
        raise AssertionError(
            f"Expected the 'vega_datasets' library to be importable in the task environment: {exc}"
        )


def test_project_dir_exists():
    assert os.path.isdir(PROJECT_DIR), (
        f"Expected project directory {PROJECT_DIR} to exist before evaluation begins."
    )


def test_solution_stub_exists():
    assert os.path.isfile(SOLUTION_FILE), (
        f"Expected an initial stub file at {SOLUTION_FILE} before evaluation begins."
    )


def test_chart_html_not_yet_present():
    chart_path = os.path.join(PROJECT_DIR, "chart.html")
    assert not os.path.exists(chart_path), (
        f"Expected {chart_path} to NOT exist before the executor runs the task."
    )
