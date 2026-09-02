"""Observation-count macro replacement."""

from __future__ import annotations

from typing import Protocol


class Executor(Protocol):
    """Minimal SQL executor required by :func:`nobs`."""

    def execute(self, sql: str) -> list[tuple[object, ...]]:
        """Execute SQL and return rows."""


def nobs(spark_or_conn: Executor, table: str) -> int:
    """Return the number of rows in a SQL table."""

    rows = spark_or_conn.execute(f"SELECT COUNT(*) FROM {table}")
    return int(rows[0][0])
