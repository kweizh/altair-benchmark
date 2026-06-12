import os
import shutil

PROJECT_DIR = "/home/user/altair_task"
BUILD_SCRIPT = os.path.join(PROJECT_DIR, "build_chart.py")


def test_python_available():
    assert shutil.which("python3") is not None, "python3 binary not found in PATH."


def test_altair_importable():
    import altair  # noqa: F401


def test_vega_datasets_importable():
    # Either the standalone vega_datasets package or altair.datasets is acceptable;
    # the task instructions reference altair.datasets, but the env must provide a
    # working barley dataset source.
    try:
        from altair.datasets import data  # type: ignore  # noqa: F401
    except Exception:
        from vega_datasets import data  # type: ignore  # noqa: F401


def test_project_dir_exists():
    assert os.path.isdir(PROJECT_DIR), f"Project directory {PROJECT_DIR} does not exist."


def test_build_script_stub_exists():
    assert os.path.isfile(BUILD_SCRIPT), (
        f"Initial build_chart.py stub not found at {BUILD_SCRIPT}."
    )


def test_output_chart_not_created_yet():
    chart_path = os.path.join(PROJECT_DIR, "output", "chart.html")
    assert not os.path.isfile(chart_path), (
        f"chart.html should not exist before the executor runs the task: {chart_path}"
    )
