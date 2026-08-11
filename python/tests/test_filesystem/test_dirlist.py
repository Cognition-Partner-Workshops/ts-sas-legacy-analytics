"""
Tests for sas_utils.filesystem.dirlist

Derived from Macro/dirlist.sas Usage block (lines 38-93).
"""

import os

import pandas as pd
import pytest

from sas_utils.filesystem.dirlist import dirlist


# ====================================================================
# Test: list files and directories
# From: %dirlist(dir=C:\Windows\System32)
# ====================================================================
class TestDirlist:
    def test_list_all(self, tmp_path):
        (tmp_path / "file1.txt").write_text("hello")
        (tmp_path / "file2.csv").write_text("a,b")
        (tmp_path / "subdir").mkdir()

        result = dirlist(tmp_path)
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 3
        expected_cols = [
            "fullname", "pathname", "filename", "basename",
            "ext", "type", "filesize", "createtime", "lastmodified",
        ]
        assert list(result.columns) == expected_cols


# ====================================================================
# Test: filter by type
# From: %dirlist(dir=..., type=f) and %dirlist(dir=..., type=d)
# ====================================================================
class TestDirlistTypeFilter:
    def test_files_only(self, tmp_path):
        (tmp_path / "file.txt").write_text("hello")
        (tmp_path / "subdir").mkdir()

        result = dirlist(tmp_path, type="f")
        assert len(result) == 1
        assert result.iloc[0]["type"] == "F"

    def test_dirs_only(self, tmp_path):
        (tmp_path / "file.txt").write_text("hello")
        (tmp_path / "subdir").mkdir()

        result = dirlist(tmp_path, type="d")
        assert len(result) == 1
        assert result.iloc[0]["type"] == "D"


# ====================================================================
# Test: custom filter function
# From: %dirlist(dir=..., filter=ext='exe')
# ====================================================================
class TestDirlistFilter:
    def test_custom_filter(self, tmp_path):
        (tmp_path / "a.txt").write_text("hello")
        (tmp_path / "b.csv").write_text("a,b")
        (tmp_path / "c.txt").write_text("world")

        result = dirlist(
            tmp_path,
            type="f",
            filter_fn=lambda row: row["ext"] == "txt",
        )
        assert len(result) == 2

    def test_basename_filter(self, tmp_path):
        (tmp_path / "alpha.txt").write_text("hello")
        (tmp_path / "beta.txt").write_text("world")

        result = dirlist(
            tmp_path,
            filter_fn=lambda row: row["basename"].startswith("a"),
        )
        assert len(result) == 1


# ====================================================================
# Test: error handling
# From: %dirlist(dir=C:\Does\Not\Exist)
# ====================================================================
class TestDirlistErrors:
    def test_path_not_exists(self):
        with pytest.raises(FileNotFoundError):
            dirlist("/nonexistent/path")

    def test_path_is_file(self, tmp_path):
        f = tmp_path / "file.txt"
        f.write_text("hello")
        with pytest.raises(NotADirectoryError):
            dirlist(f)

    def test_empty_directory(self, tmp_path):
        result = dirlist(tmp_path)
        assert len(result) == 0
