import importlib
import os

import pytest

PROJECT_DIR = "/home/user/iris_chart"


def test_altair_importable():
    try:
        importlib.import_module("altair")
    except ImportError as exc:
        pytest.fail(f"Expected 'altair' to be importable in the task environment: {exc}")


def test_vega_datasets_importable():
    try:
        importlib.import_module("vega_datasets")
    except ImportError as exc:
        pytest.fail(
            f"Expected 'vega_datasets' to be importable in the task environment: {exc}"
        )


def test_project_dir_exists():
    assert os.path.isdir(PROJECT_DIR), (
        f"Project directory {PROJECT_DIR} does not exist; the initial scaffold is missing."
    )


def test_initial_stub_script_present():
    stub_path = os.path.join(PROJECT_DIR, "chart.py")
    assert os.path.isfile(stub_path), (
        f"Initial stub {stub_path} is missing; the executor should start from this file."
    )
