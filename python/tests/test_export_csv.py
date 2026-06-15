"""Tests for sas_transforms.export_csv — mirrors SAS %export_csv macro."""

import pandas as pd
import pytest

from sas_transforms.export_csv import export_csv


class TestExportCsv:
    def test_basic_export(self, class_df: pd.DataFrame, tmp_path) -> None:
        out = export_csv(class_df, str(tmp_path / "class.csv"))
        result = pd.read_csv(out)
        assert list(result.columns) == list(class_df.columns)
        assert len(result) == len(class_df)

    def test_no_header(self, class_df: pd.DataFrame, tmp_path) -> None:
        out = export_csv(class_df, str(tmp_path / "class.csv"), header=False)
        result = pd.read_csv(out, header=None)
        assert len(result) == len(class_df)

    def test_label_header(self, class_df: pd.DataFrame, tmp_path) -> None:
        labels = {"Name": "Student Name", "Sex": "Gender", "Age": "Age In Years"}
        out = export_csv(
            class_df,
            str(tmp_path / "class.csv"),
            label=True,
            labels=labels,
        )
        result = pd.read_csv(out)
        assert "Student Name" in result.columns
        assert "Gender" in result.columns
        assert "Age In Years" in result.columns

    def test_directory_path(self, class_df: pd.DataFrame, tmp_path) -> None:
        """When path is a directory, filename is derived from DataFrame name."""
        class_df.name = "students"
        out = export_csv(class_df, str(tmp_path))
        assert out.endswith("students.csv")
        result = pd.read_csv(out)
        assert len(result) == len(class_df)

    def test_replace_false_raises(self, class_df: pd.DataFrame, tmp_path) -> None:
        path = str(tmp_path / "class.csv")
        export_csv(class_df, path, replace=True)
        with pytest.raises(FileExistsError):
            export_csv(class_df, path, replace=False)

    def test_replace_true_overwrites(self, class_df: pd.DataFrame, tmp_path) -> None:
        path = str(tmp_path / "class.csv")
        export_csv(class_df, path, replace=True)
        export_csv(class_df, path, replace=True)  # should not raise

    def test_nonexistent_directory(self, class_df: pd.DataFrame, tmp_path) -> None:
        with pytest.raises(FileNotFoundError):
            export_csv(class_df, str(tmp_path / "nodir" / "class.csv"))
