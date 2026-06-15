"""Tests for sas_transforms.export_xlsx — mirrors SAS %export_xlsx macro."""

import pandas as pd
import pytest

from sas_transforms.export_xlsx import export_xlsx


@pytest.fixture()
def sample_df() -> pd.DataFrame:
    df = pd.DataFrame({
        "Name": ["Alfred", "Alice", "Barbara"],
        "Age": [14, 13, 13],
        "Height": [69.0, 56.5, 65.3],
    })
    df.name = "class"
    return df


class TestExportXLSX:
    def test_basic_export(self, sample_df: pd.DataFrame, tmp_path):
        out = export_xlsx(sample_df, tmp_path / "test.xlsx", replace=True)
        assert out.exists()
        loaded = pd.read_excel(out, engine="openpyxl")
        assert list(loaded.columns) == ["Name", "Age", "Height"]
        assert len(loaded) == 3

    def test_directory_derives_filename(self, sample_df: pd.DataFrame, tmp_path):
        out = export_xlsx(sample_df, tmp_path, replace=True)
        assert out.name == "class.xlsx"

    def test_replace_false_raises(self, sample_df: pd.DataFrame, tmp_path):
        path = tmp_path / "test.xlsx"
        export_xlsx(sample_df, path, replace=True)
        with pytest.raises(FileExistsError):
            export_xlsx(sample_df, path, replace=False)

    def test_label_header(self, sample_df: pd.DataFrame, tmp_path):
        sample_df.attrs["_labels"] = {"Name": "Student Name", "Height": "Height (in)"}
        path = tmp_path / "labels.xlsx"
        export_xlsx(sample_df, path, replace=True, label=True)
        loaded = pd.read_excel(path, engine="openpyxl")
        assert "Student Name" in loaded.columns
        assert "Height (in)" in loaded.columns

    def test_roundtrip_values(self, sample_df: pd.DataFrame, tmp_path):
        path = tmp_path / "roundtrip.xlsx"
        export_xlsx(sample_df, path, replace=True)
        loaded = pd.read_excel(path, engine="openpyxl")
        assert loaded["Age"].tolist() == [14, 13, 13]
        assert loaded["Height"].tolist() == pytest.approx([69.0, 56.5, 65.3])
