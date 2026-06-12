import importlib
import os

PROJECT_DIR = "/home/user/myproject"


def test_altair_importable():
    try:
        importlib.import_module("altair")
    except ImportError as exc:  # pragma: no cover - explicit assertion below
        raise AssertionError(
            "The 'altair' library must be importable in the environment."
        ) from exc


def test_vega_datasets_importable():
    try:
        importlib.import_module("vega_datasets")
    except ImportError as exc:  # pragma: no cover - explicit assertion below
        raise AssertionError(
            "The 'vega_datasets' library must be importable in the environment."
        ) from exc


def test_project_dir_exists():
    assert os.path.isdir(PROJECT_DIR), (
        f"Project directory {PROJECT_DIR} must exist before the task starts."
    )


def test_project_dir_has_stub():
    stub_path = os.path.join(PROJECT_DIR, "main.py")
    assert os.path.isfile(stub_path), (
        f"Stub entry point {stub_path} must exist before the task starts."
    )
