import os
import shutil
import subprocess

PROJECT_DIR = "/home/user/myproject"
CHART_SCRIPT = os.path.join(PROJECT_DIR, "chart.py")


def test_python3_available():
    assert shutil.which("python3") is not None, "python3 binary not found in PATH."


def test_altair_importable():
    result = subprocess.run(
        ["python3", "-c", "import altair"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        "Failed to import altair in the environment: "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )


def test_vega_datasets_importable():
    result = subprocess.run(
        ["python3", "-c", "from vega_datasets import data; _ = data.airports.url"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        "Failed to import vega_datasets in the environment: "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )


def test_project_dir_exists():
    assert os.path.isdir(PROJECT_DIR), f"Project directory {PROJECT_DIR} does not exist."


def test_chart_stub_exists():
    assert os.path.isfile(CHART_SCRIPT), (
        f"Initial stub script {CHART_SCRIPT} does not exist."
    )


def test_chart_html_not_yet_generated():
    html_path = os.path.join(PROJECT_DIR, "chart.html")
    assert not os.path.exists(html_path), (
        f"Expected {html_path} to NOT exist before the task is executed, "
        "but it already does."
    )
