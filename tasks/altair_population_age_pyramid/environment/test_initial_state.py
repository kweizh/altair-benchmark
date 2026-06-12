import os

import pytest

PROJECT_DIR = "/home/user/myproject"


def test_altair_importable():
    try:
        import altair  # noqa: F401
    except ImportError as exc:
        pytest.fail(f"Altair is not importable in the environment: {exc}")


def test_altair_datasets_importable():
    try:
        from altair.datasets import data  # noqa: F401
    except ImportError as exc:
        pytest.fail(f"altair.datasets is not importable in the environment: {exc}")


def test_project_directory_exists():
    assert os.path.isdir(PROJECT_DIR), (
        f"Project directory {PROJECT_DIR} is expected to be present in the initial environment."
    )


def test_build_pyramid_script_exists():
    script_path = os.path.join(PROJECT_DIR, "build_pyramid.py")
    assert os.path.isfile(script_path), (
        f"Initial stub script {script_path} is expected to be present in the initial environment."
    )


def test_pyramid_html_not_present_yet():
    out_path = os.path.join(PROJECT_DIR, "pyramid.html")
    assert not os.path.exists(out_path), (
        f"{out_path} must NOT exist in the initial environment; the executor is responsible for creating it."
    )


def test_pyramid_spec_not_present_yet():
    out_path = os.path.join(PROJECT_DIR, "pyramid_spec.json")
    assert not os.path.exists(out_path), (
        f"{out_path} must NOT exist in the initial environment; the executor is responsible for creating it."
    )
