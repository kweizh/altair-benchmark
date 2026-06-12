"""Initial-state verification for the `altair_unemployment_streamgraph` task.

Confirms that the evaluation environment is correctly provisioned before the
executor begins: the project directory exists, Python 3 and Altair are
installed, and no stale solution / artifact remains from a prior run.
"""

import os
import shutil
import subprocess

PROJECT_DIR = "/home/user/myproject"


def test_python3_available():
    assert shutil.which("python3") is not None, "python3 binary not found in PATH."


def test_altair_importable():
    """Ensure Vega-Altair is installed and importable from python3."""
    result = subprocess.run(
        ["python3", "-c", "import altair as alt; print(alt.__version__)"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        f"Could not import altair: stdout={result.stdout!r} stderr={result.stderr!r}"
    )
    version = result.stdout.strip()
    assert version, "altair.__version__ was empty."


def test_project_dir_exists():
    assert os.path.isdir(PROJECT_DIR), (
        f"Project directory {PROJECT_DIR} does not exist."
    )


def test_solution_script_absent_initially():
    """The agent is expected to create solution.py; it must not exist yet."""
    entry = os.path.join(PROJECT_DIR, "solution.py")
    assert not os.path.exists(entry), (
        f"solution.py already exists at {entry}; the agent must create it."
    )


def test_chart_html_absent_initially():
    """The solution's output file must not exist before evaluation starts."""
    chart_path = os.path.join(PROJECT_DIR, "out", "chart.html")
    assert not os.path.exists(chart_path), (
        f"Pre-existing chart artifact found at {chart_path}; "
        "the environment must be clean before evaluation."
    )
