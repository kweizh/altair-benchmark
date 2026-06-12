import importlib
import os
import shutil

PROJECT_DIR = "/home/user/myproject"


def test_python3_available():
    assert shutil.which("python3") is not None, "python3 binary not found in PATH."


def test_altair_importable():
    try:
        importlib.import_module("altair")
    except Exception as exc:  # pragma: no cover - diagnostic
        raise AssertionError(
            f"Expected the altair package to be importable, but import failed: {exc}"
        )


def test_vega_datasets_importable():
    try:
        importlib.import_module("vega_datasets")
    except Exception as exc:  # pragma: no cover - diagnostic
        raise AssertionError(
            "Expected the vega_datasets package to be importable so the task can "
            f"reference data.stocks.url, but import failed: {exc}"
        )


def test_project_directory_exists():
    assert os.path.isdir(PROJECT_DIR), (
        f"Expected the project working directory {PROJECT_DIR} to already exist "
        "before the agent starts working."
    )


def test_chart_html_not_yet_created():
    chart_path = os.path.join(PROJECT_DIR, "chart.html")
    assert not os.path.exists(chart_path), (
        f"Expected the chart artifact {chart_path} to NOT exist before the agent "
        "runs the task; it should be produced by the agent's build script."
    )
