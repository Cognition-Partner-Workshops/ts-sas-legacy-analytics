"""Shared fixtures for SAS-to-Python translation tests."""

import pandas as pd
import pytest


@pytest.fixture()
def class_df() -> pd.DataFrame:
    """Minimal replica of ``sashelp.class`` used in the SAS macro examples."""
    return pd.DataFrame({
        "Name": [
            "Alfred", "Alice", "Barbara", "Carol", "Henry",
            "James", "Jane", "Janet", "Jeffrey", "John",
            "Joyce", "Judy", "Louise", "Mary", "Philip",
            "Robert", "Ronald", "Thomas", "William",
        ],
        "Sex": [
            "M", "F", "F", "F", "M",
            "M", "F", "F", "M", "M",
            "F", "F", "F", "F", "M",
            "M", "M", "M", "M",
        ],
        "Age": [
            14, 13, 13, 14, 14,
            12, 12, 15, 13, 12,
            11, 14, 12, 15, 16,
            12, 15, 11, 15,
        ],
        "Height": [
            69.0, 56.5, 65.3, 62.8, 63.5,
            57.3, 59.8, 62.5, 62.5, 59.0,
            51.3, 64.3, 56.3, 66.5, 72.0,
            64.8, 67.0, 57.5, 66.5,
        ],
        "Weight": [
            112.5, 84.0, 98.0, 102.5, 102.5,
            83.0, 84.5, 112.5, 84.0, 99.5,
            50.5, 90.0, 77.0, 112.0, 150.0,
            128.0, 133.0, 85.0, 112.0,
        ],
    })


@pytest.fixture()
def vitals_df() -> pd.DataFrame:
    """Small dataset mimicking clinical vitals for transpose tests."""
    return pd.DataFrame({
        "subject": ["S1", "S1", "S1", "S2", "S2", "S2"],
        "visit": ["V1", "V1", "V1", "V1", "V1", "V1"],
        "param": ["DIABP", "SYSBP", "TEMP", "DIABP", "SYSBP", "TEMP"],
        "value": [80, 120, 36.6, 75, 115, 37.0],
    })
