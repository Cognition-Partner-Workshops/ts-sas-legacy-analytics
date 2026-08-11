"""
Tests for sas_utils.reporting.logparse

Derived from Macro/logparse.sas.
"""

import pytest

from sas_utils.reporting.logparse import logparse


class TestLogparse:
    def test_parse_errors(self, tmp_path):
        log = tmp_path / "test.log"
        log.write_text(
            "NOTE: Starting job\n"
            "WARNING: Variable is uninitialized\n"
            "ERROR: File not found\n"
            "NOTE: Job completed\n"
        )
        report = logparse(log)
        assert report.total_lines == 4
        assert len(report.errors) == 1
        assert len(report.warnings) == 1
        assert len(report.notes) == 2
        assert report.has_errors is True
        assert report.has_warnings is True

    def test_clean_log(self, tmp_path):
        log = tmp_path / "clean.log"
        log.write_text("NOTE: Everything is fine\nNOTE: Done\n")
        report = logparse(log)
        assert report.has_errors is False
        assert report.has_warnings is False

    def test_filter_levels(self, tmp_path):
        log = tmp_path / "test.log"
        log.write_text(
            "ERROR: Something bad\n"
            "WARNING: Something iffy\n"
            "NOTE: All good\n"
        )
        report = logparse(log, levels=["ERROR"])
        assert len(report.entries) == 1
        assert report.entries[0].level == "ERROR"

    def test_file_not_found(self):
        with pytest.raises(FileNotFoundError):
            logparse("/nonexistent/file.log")

    def test_summary(self, tmp_path):
        log = tmp_path / "test.log"
        log.write_text("ERROR: fail\n")
        report = logparse(log)
        summary = report.summary()
        assert "Errors: 1" in summary
