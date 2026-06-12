import importlib
import os

PROJECT_DIR = "/home/user/myproject"


def test_altair_library_importable():
    altair = importlib.import_module("altair")
    assert altair is not None, "Altair library is not importable in the environment."


def test_vega_datasets_importable():
    vega_datasets = importlib.import_module("vega_datasets")
    assert vega_datasets is not None, (
        "vega_datasets is not importable; it is required to access data.movies.url."
    )


def test_project_directory_exists():
    assert os.path.isdir(PROJECT_DIR), (
        f"Project directory {PROJECT_DIR} does not exist in the initial environment."
    )


def test_chart_html_not_created_yet():
    chart_path = os.path.join(PROJECT_DIR, "chart.html")
    assert not os.path.exists(chart_path), (
        f"chart.html should not exist before the task starts, but found {chart_path}."
    )
