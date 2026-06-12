import os

import pytest

PROJECT_DIR = "/home/user/myproject"


def test_altair_importable():
    try:
        import altair  # noqa: F401
    except Exception as exc:  # pragma: no cover - import failure surfaces in assert
        pytest.fail(f"Failed to import altair: {exc}")


def test_vega_datasets_importable():
    try:
        import vega_datasets  # noqa: F401
    except Exception as exc:  # pragma: no cover
        pytest.fail(f"Failed to import vega_datasets: {exc}")


def test_project_dir_exists():
    assert os.path.isdir(PROJECT_DIR), (
        f"Expected project directory {PROJECT_DIR} to exist before evaluation."
    )


def test_chart_html_not_present_initially():
    chart_path = os.path.join(PROJECT_DIR, "chart.html")
    assert not os.path.exists(chart_path), (
        "chart.html should not exist before the executor runs the task; "
        "the executor is responsible for generating it."
    )
