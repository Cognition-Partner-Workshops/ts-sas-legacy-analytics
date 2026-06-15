"""Tests for sas_transforms.export_xlsx — mirrors SAS %export_xlsx macro."""

import pandas as pd
import pytest

from sas_transforms.export_xlsx import export_xlsx


class TestExportXlsx:
    def test_basic_export(self, class_df: pd.DataFrame, tmp_path) -> None:
        out = export_xlsx(class_df, str(tmp_path / "class.xlsx"))
        result = pd.read_excel(out, engine="openpyxl")
        assert list(result.columns) == list(class_df.columns)
        assert len(result) == len(class_df)

    def test_label_header(self, class_df: pd.DataFrame, tmp_path) -> None:
        labels = {"Name": "Student Name", "Age": "Age In Years"}
        out = export_xlsx(
            class_df,
            str(tmp_path / "class.xlsx"),
            label=True,
            labels=labels,
        )
        result = pd.read_excel(out, engine="openpyxl")
        assert "Student Name" in result.columns
        assert "Age In Years" in result.columns

    def test_directory_path(self, class_df: pd.DataFrame, tmp_path) -> None:
        class_df.name = "students"
        out = export_xlsx(class_df, str(tmp_path))
        assert out.endswith("students.xlsx")

    def test_replace_false_raises(self, class_df: pd.DataFrame, tmp_path) -> None:
        path = str(tmp_path / "class.xlsx")
        export_xlsx(class_df, path, replace=True)
        with pytest.raises(FileExistsError):
            export_xlsx(class_df, path, replace=False)

    def test_replace_true_overwrites(self, class_df: pd.DataFrame, tmp_path) -> None:
        path = str(tmp_path / "class.xlsx")
        export_xlsx(class_df, path, replace=True)
        export_xlsx(class_df, path, replace=True)

    def test_nonexistent_directory(self, class_df: pd.DataFrame, tmp_path) -> None:
        with pytest.raises(FileNotFoundError):
            export_xlsx(class_df, str(tmp_path / "nodir" / "class.xlsx"))
