import importlib
import os

import pytest

PROJECT_DIR = "/home/user/altair_project"


def test_altair_importable():
    try:
        importlib.import_module("altair")
    except Exception as exc:  # pragma: no cover - import diagnostics only
        pytest.fail(f"altair package is not importable: {exc!r}")


def test_vega_datasets_importable():
    try:
        importlib.import_module("vega_datasets")
    except Exception as exc:  # pragma: no cover - import diagnostics only
        pytest.fail(f"vega_datasets package is not importable: {exc!r}")


def test_project_dir_exists():
    assert os.path.isdir(PROJECT_DIR), (
        f"Project directory {PROJECT_DIR} does not exist."
    )


def test_no_partial_solution_chart_html():
    chart_html = os.path.join(PROJECT_DIR, "chart.html")
    assert not os.path.exists(chart_html), (
        f"Initial state must not contain a pre-built chart at {chart_html}."
    )


def test_no_partial_solution_build_script():
    build_script = os.path.join(PROJECT_DIR, "build_chart.py")
    assert not os.path.exists(build_script), (
        f"Initial state must not contain a pre-built build script at {build_script}."
    )
