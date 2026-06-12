import importlib
import os


PROJECT_DIR = "/home/user/altair_choropleth_app"


def test_altair_is_importable():
    try:
        importlib.import_module("altair")
    except Exception as exc:  # pragma: no cover - defensive
        raise AssertionError(
            f"Expected the `altair` package to be importable in the task environment, but got: {exc!r}"
        )


def test_altair_datasets_is_importable():
    try:
        importlib.import_module("altair.datasets")
    except Exception as exc:  # pragma: no cover - defensive
        raise AssertionError(
            "Expected `altair.datasets` (the bundled sample datasets entry point) to be importable, "
            f"but got: {exc!r}"
        )


def test_project_dir_exists():
    assert os.path.isdir(PROJECT_DIR), (
        f"Expected the project directory {PROJECT_DIR} to be created by the initial state setup."
    )


def test_no_prebuilt_chart_html():
    chart_path = os.path.join(PROJECT_DIR, "chart.html")
    assert not os.path.exists(chart_path), (
        f"Expected {chart_path} to NOT exist before the executor runs the task, "
        "but a pre-built chart was found."
    )
