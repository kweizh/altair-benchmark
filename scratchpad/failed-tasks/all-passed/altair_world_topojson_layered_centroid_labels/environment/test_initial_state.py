import importlib
import os

PROJECT_DIR = "/home/user/myproject"


def test_altair_importable():
    try:
        importlib.import_module("altair")
    except ImportError as exc:  # pragma: no cover
        raise AssertionError(
            f"altair is not importable in the task environment: {exc}"
        )


def test_vega_datasets_importable():
    try:
        importlib.import_module("vega_datasets")
    except ImportError as exc:  # pragma: no cover
        raise AssertionError(
            f"vega_datasets is not importable in the task environment: {exc}"
        )


def test_pandas_importable():
    try:
        importlib.import_module("pandas")
    except ImportError as exc:  # pragma: no cover
        raise AssertionError(
            f"pandas is not importable in the task environment: {exc}"
        )


def test_project_dir_exists():
    assert os.path.isdir(PROJECT_DIR), (
        f"Expected project directory {PROJECT_DIR} to exist before the task starts."
    )
