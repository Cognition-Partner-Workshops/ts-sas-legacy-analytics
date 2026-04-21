"""
Log parsing utility.

Migrated from: Macro/logparse.sas
Original author: Scott Bass

Parses log files for errors, warnings, and notes, producing a summary report.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Sequence, Union


@dataclass
class LogEntry:
    """A single log entry."""
    line_num: int
    level: str  # "ERROR", "WARNING", "NOTE"
    message: str


@dataclass
class LogReport:
    """Summary of log parsing results."""
    filename: str
    entries: list[LogEntry] = field(default_factory=list)
    total_lines: int = 0

    @property
    def errors(self) -> list[LogEntry]:
        return [e for e in self.entries if e.level == "ERROR"]

    @property
    def warnings(self) -> list[LogEntry]:
        return [e for e in self.entries if e.level == "WARNING"]

    @property
    def notes(self) -> list[LogEntry]:
        return [e for e in self.entries if e.level == "NOTE"]

    @property
    def has_errors(self) -> bool:
        return len(self.errors) > 0

    @property
    def has_warnings(self) -> bool:
        return len(self.warnings) > 0

    def summary(self) -> str:
        lines = [
            f"Log: {self.filename}",
            f"Total lines: {self.total_lines}",
            f"Errors: {len(self.errors)}",
            f"Warnings: {len(self.warnings)}",
            f"Notes: {len(self.notes)}",
        ]
        return "\n".join(lines)


_PATTERNS = {
    "ERROR": re.compile(r"^ERROR[:\s]", re.IGNORECASE),
    "WARNING": re.compile(r"^WARNING[:\s]", re.IGNORECASE),
    "NOTE": re.compile(r"^NOTE[:\s]", re.IGNORECASE),
}


def logparse(
    path: Union[str, Path],
    levels: Optional[Sequence[str]] = None,
) -> LogReport:
    """
    Parse a log file for errors, warnings, and notes.

    Parameters
    ----------
    path : str or Path
        Path to the log file.
    levels : list of str, optional
        Levels to scan for. Default: all (``ERROR``, ``WARNING``, ``NOTE``).

    Returns
    -------
    LogReport
        Parsed log results.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Log file {str(path)!r} does not exist.")

    if levels is None:
        levels = ["ERROR", "WARNING", "NOTE"]
    levels_upper = {l.upper() for l in levels}

    report = LogReport(filename=str(path))
    patterns = {k: v for k, v in _PATTERNS.items() if k in levels_upper}

    with open(path, "r", errors="replace") as f:
        for line_num, line in enumerate(f, 1):
            report.total_lines = line_num
            stripped = line.strip()
            for level, pattern in patterns.items():
                if pattern.match(stripped):
                    report.entries.append(LogEntry(
                        line_num=line_num,
                        level=level,
                        message=stripped,
                    ))
                    break

    return report
