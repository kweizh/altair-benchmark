import csv
import importlib
import os

PROJECT_DIR = "/home/user/altair_stocks_candlestick"
CSV_PATH = os.path.join(PROJECT_DIR, "ohlcv.csv")

REQUIRED_COLUMNS = ["date", "open", "high", "low", "close", "volume"]


def test_altair_importable():
    """The target library (Vega-Altair) must be installed and importable."""
    altair = importlib.import_module("altair")
    assert altair is not None, "Vega-Altair (`altair`) is not importable in the environment."


def test_pandas_importable():
    """Pandas is required for reading the provided CSV."""
    pandas = importlib.import_module("pandas")
    assert pandas is not None, "pandas is not importable in the environment."


def test_project_directory_exists():
    assert os.path.isdir(PROJECT_DIR), (
        f"Project directory {PROJECT_DIR} does not exist."
    )


def test_ohlcv_csv_exists():
    assert os.path.isfile(CSV_PATH), (
        f"Initial OHLCV dataset {CSV_PATH} does not exist."
    )


def test_ohlcv_csv_has_required_columns():
    with open(CSV_PATH, newline="") as f:
        reader = csv.reader(f)
        try:
            header = next(reader)
        except StopIteration:
            raise AssertionError(f"{CSV_PATH} is empty; expected a CSV header row.")

    missing = [col for col in REQUIRED_COLUMNS if col not in header]
    assert not missing, (
        f"OHLCV CSV {CSV_PATH} is missing required columns: {missing}. "
        f"Found header: {header}."
    )


def test_ohlcv_csv_has_minimum_rows():
    with open(CSV_PATH, newline="") as f:
        reader = csv.reader(f)
        rows = list(reader)
    # Subtract 1 for the header row.
    data_rows = len(rows) - 1
    assert data_rows >= 60, (
        f"OHLCV CSV {CSV_PATH} must contain at least 60 data rows; found {data_rows}."
    )
