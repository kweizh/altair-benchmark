import importlib
import os

PROJECT_DIR = "/home/user/myproject"


def test_project_dir_exists():
    assert os.path.isdir(PROJECT_DIR), (
        f"Expected project directory {PROJECT_DIR} to exist before the task starts."
    )


def test_altair_importable():
    try:
        importlib.import_module("altair")
    except Exception as exc:  # pragma: no cover - failure surface
        raise AssertionError(
            f"Expected the 'altair' package to be importable in the environment, "
            f"but importing it failed with: {exc!r}"
        )


def test_vega_datasets_importable():
    try:
        importlib.import_module("vega_datasets")
    except Exception as exc:  # pragma: no cover - failure surface
        raise AssertionError(
            f"Expected the 'vega_datasets' package to be importable in the environment, "
            f"but importing it failed with: {exc!r}"
        )


def test_no_chart_artifacts_yet():
    # The task should produce these files; they must not already exist.
    for name in ("chart.html", "chart.json"):
        path = os.path.join(PROJECT_DIR, name)
        assert not os.path.exists(path), (
            f"Initial state expects {path} to be absent before the task runs, "
            f"but it already exists."
        )
