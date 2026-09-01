"""Excel export compatibility shim."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from pathlib import Path

from openpyxl import Workbook


def export_xlsx(
    rows: Iterable[Mapping[str, object]],
    path: str,
    sheet: str = "Sheet1",
    header: bool = True,
) -> str:
    """Write mappings to an XLSX worksheet and return the output path."""

    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    workbook = Workbook()
    worksheet = workbook.active
    worksheet.title = sheet
    records = list(rows)
    keys = list(records[0]) if records else []
    if header:
        worksheet.append(keys)
    for record in records:
        worksheet.append([record.get(key) for key in keys])
    workbook.save(output)
    return str(output)
