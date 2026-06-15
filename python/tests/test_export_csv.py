"""Tests for sas_transforms.export_csv — mirrors SAS %export_csv macro."""

import pandas as pd
import pytest

from sas_transforms.export_csv import export_csv


@pytest.fixture()
def sample_df() -> pd.DataFrame:
    df = pd.DataFrame({
        "Name": ["Alfred", "Alice", "Barbara"],
        "Age": [14, 13, 13],
        "Height": [69.0, 56.5, 65.3],
    })
    df.name = "class"
    return df


class TestExportCSV:
    def test_basic_export(self, sample_df: pd.DataFrame, tmp_path):
        out = export_csv(sample_df, tmp_path / "test.csv", replace=True)
        assert out.exists()
        loaded = pd.read_csv(out)
        assert list(loaded.columns) == ["Name", "Age", "Height"]
        assert len(loaded) == 3

    def test_directory_derives_filename(self, sample_df: pd.DataFrame, tmp_path):
        out = export_csv(sample_df, tmp_path, replace=True)
        assert out.name == "class.csv"
        assert out.exists()

    def test_replace_false_raises(self, sample_df: pd.DataFrame, tmp_path):
        path = tmp_path / "test.csv"
        export_csv(sample_df, path, replace=True)
        with pytest.raises(FileExistsError):
            export_csv(sample_df, path, replace=False)

    def test_replace_true_overwrites(self, sample_df: pd.DataFrame, tmp_path):
        path = tmp_path / "test.csv"
        export_csv(sample_df, path, replace=True)
        export_csv(sample_df, path, replace=True)
        loaded = pd.read_csv(path)
        assert len(loaded) == 3

    def test_no_header(self, sample_df: pd.DataFrame, tmp_path):
        path = tmp_path / "no_header.csv"
        export_csv(sample_df, path, replace=True, header=False)
        with open(path) as f:
            first_line = f.readline().strip()
        assert first_line.startswith("Alfred")

    def test_label_header(self, sample_df: pd.DataFrame, tmp_path):
        sample_df.attrs["_labels"] = {"Name": "Student Name", "Age": "Age In Years"}
        path = tmp_path / "labels.csv"
        export_csv(sample_df, path, replace=True, label=True)
        loaded = pd.read_csv(path)
        assert "Student Name" in loaded.columns
        assert "Age In Years" in loaded.columns

    def test_tab_delimiter(self, sample_df: pd.DataFrame, tmp_path):
        path = tmp_path / "test.tsv"
        export_csv(sample_df, path, replace=True, delimiter="\t")
        with open(path) as f:
            first_line = f.readline()
        assert "\t" in first_line
