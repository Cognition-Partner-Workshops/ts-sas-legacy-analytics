"""Tests for sas_transforms.export_dbms — mirrors SAS %export_dbms macro."""

import pandas as pd
import pytest

from sas_transforms.export_dbms import export_dbms


@pytest.fixture()
def sample_df() -> pd.DataFrame:
    df = pd.DataFrame({
        "Name": ["Alfred", "Alice", "Barbara"],
        "Age": [14, 13, 13],
        "Height": [69.0, 56.5, 65.3],
    })
    df.name = "class"
    return df


class TestExportDbms:
    def test_xlsx_default(self, sample_df: pd.DataFrame, tmp_path):
        out = export_dbms(sample_df, tmp_path / "test.xlsx", replace=True)
        assert out.suffix == ".xlsx"
        loaded = pd.read_excel(out, engine="openpyxl")
        assert len(loaded) == 3

    def test_dir_derives_filename_xlsx(self, sample_df: pd.DataFrame, tmp_path):
        out = export_dbms(sample_df, tmp_path, replace=True)
        assert out.name == "class.xlsx"

    def test_invalid_dbms_raises(self, sample_df: pd.DataFrame, tmp_path):
        with pytest.raises(ValueError, match="Unsupported dbms"):
            export_dbms(sample_df, tmp_path, dbms="parquet", replace=True)

    def test_replace_false_raises(self, sample_df: pd.DataFrame, tmp_path):
        path = tmp_path / "test.xlsx"
        export_dbms(sample_df, path, replace=True)
        with pytest.raises(FileExistsError):
            export_dbms(sample_df, path, replace=False)

    def test_label_flag(self, sample_df: pd.DataFrame, tmp_path):
        sample_df.attrs["_labels"] = {"Name": "Full Name"}
        out = export_dbms(sample_df, tmp_path / "labels.xlsx", replace=True, label=True)
        loaded = pd.read_excel(out, engine="openpyxl")
        assert "Full Name" in loaded.columns

    def test_bak_cleanup(self, sample_df: pd.DataFrame, tmp_path):
        path = tmp_path / "test.xlsx"
        bak = tmp_path / "test.xlsx.bak"
        bak.touch()
        export_dbms(sample_df, path, replace=True)
        assert not bak.exists()

    def test_stata_export(self, sample_df: pd.DataFrame, tmp_path):
        out = export_dbms(sample_df, tmp_path / "test.dta", dbms="stata", replace=True)
        assert out.suffix == ".dta"
        assert out.exists()
        loaded = pd.read_stata(out)
        assert len(loaded) == 3

    def test_derives_extension_from_dbms(self, sample_df: pd.DataFrame, tmp_path):
        out = export_dbms(sample_df, tmp_path / "noext", dbms="xlsx", replace=True)
        assert out.suffix == ".xlsx"
