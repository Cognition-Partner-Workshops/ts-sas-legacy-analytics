"""Shared fixtures for the SAS-to-Python translation test suite."""

import pandas as pd
import pytest


@pytest.fixture()
def class_df() -> pd.DataFrame:
    """SAS ``sashelp.class`` — 19 students with Name, Sex, Age, Height, Weight."""
    return pd.DataFrame(
        {
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
        }
    )


@pytest.fixture()
def vitals_df() -> pd.DataFrame:
    """Simulated clinical vitals dataset for transpose tests."""
    return pd.DataFrame(
        {
            "studyid": ["S1"] * 6,
            "usubjid": ["P001"] * 3 + ["P002"] * 3,
            "visit": ["V1", "V2", "V3"] * 2,
            "diabp": [70, 72, 68, 80, 78, 82],
            "sysbp": [120, 118, 122, 140, 138, 142],
            "pulse": [60, 62, 58, 75, 73, 77],
        }
    )
