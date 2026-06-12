import os

PROJECT_DIR = "/home/user/myproject"
SOLUTION_PATH = os.path.join(PROJECT_DIR, "solution.py")


def test_altair_importable():
    try:
        import altair  # noqa: F401
    except Exception as exc:  # pragma: no cover - import error surfaces here
        raise AssertionError(
            f"altair must be importable in the task environment but raised: {exc!r}"
        )


def test_project_directory_exists():
    assert os.path.isdir(PROJECT_DIR), (
        f"Project directory {PROJECT_DIR} must exist before the task starts."
    )


def test_solution_stub_exists():
    assert os.path.isfile(SOLUTION_PATH), (
        f"Initial stub {SOLUTION_PATH} must be present at the start of the task."
    )


def test_chart_html_not_yet_created():
    chart_path = os.path.join(PROJECT_DIR, "chart.html")
    assert not os.path.exists(chart_path), (
        "chart.html should not exist before the task is executed; the solver creates it."
    )
