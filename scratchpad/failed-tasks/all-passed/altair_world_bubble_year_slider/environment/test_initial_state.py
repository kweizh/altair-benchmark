import os
import importlib

PROJECT_DIR = "/home/user/myproject"


def test_altair_importable():
    altair = importlib.import_module("altair")
    assert altair is not None, "altair package is not importable."


def test_vega_datasets_importable():
    vd = importlib.import_module("vega_datasets")
    assert vd is not None, "vega_datasets package is not importable."


def test_project_dir_exists():
    assert os.path.isdir(PROJECT_DIR), (
        f"Project directory {PROJECT_DIR} does not exist."
    )


def test_chart_html_not_yet_created():
    chart_path = os.path.join(PROJECT_DIR, "chart.html")
    assert not os.path.exists(chart_path), (
        f"chart.html at {chart_path} must not exist before the task starts."
    )


def test_spec_json_not_yet_created():
    spec_path = os.path.join(PROJECT_DIR, "spec.json")
    assert not os.path.exists(spec_path), (
        f"spec.json at {spec_path} must not exist before the task starts."
    )
