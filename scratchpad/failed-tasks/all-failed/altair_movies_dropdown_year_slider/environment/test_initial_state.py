import os
import shutil


PROJECT_DIR = "/home/user/project"


def test_python_available():
    assert shutil.which("python3") is not None, "python3 is not available in PATH."


def test_altair_importable():
    import altair  # noqa: F401

    assert altair is not None, "altair (vega-altair) is not importable in the environment."


def test_vega_datasets_importable():
    from vega_datasets import data  # noqa: F401

    assert data.movies.url.endswith(
        "movies.json"
    ), "vega_datasets.data.movies.url should resolve to a movies.json file."


def test_pochi_verifier_available():
    assert shutil.which("pochi-verifier") is not None, (
        "pochi-verifier CLI is required for browser-based verification but was not found in PATH."
    )


def test_project_dir_exists():
    assert os.path.isdir(PROJECT_DIR), f"Project directory {PROJECT_DIR} does not exist."


def test_dashboard_html_not_yet_present():
    # The executor is responsible for producing this artifact; it must not exist initially.
    html_path = os.path.join(PROJECT_DIR, "movies_dashboard.html")
    assert not os.path.exists(html_path), (
        f"{html_path} should not exist before the task is executed."
    )
