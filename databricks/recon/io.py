"""Reference / local-target CSV loading and manifest handling."""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

Rows = list[dict[str, str | None]]


class ReferenceMissing(SystemExit):
    def __init__(self, what: str):
        super().__init__(f"reference missing: {what}")


def read_csv(path: Path) -> Rows:
    with path.open(newline="", encoding="utf-8") as fh:
        rdr = csv.DictReader(fh)
        rows: Rows = []
        for raw in rdr:
            rows.append({k.lower(): (v if v != "" else None) for k, v in raw.items() if k})
        return rows


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load_reference_manifest(ref_dir: Path) -> tuple[dict, str]:
    """Return (manifest json, sha256 of manifest file); fail clearly when absent."""
    if not ref_dir.is_dir():
        raise ReferenceMissing(f"directory {ref_dir} does not exist (W0-R output not present)")
    mpath = ref_dir / "manifest.json"
    if not mpath.is_file():
        raise ReferenceMissing(f"{mpath} does not exist")
    return json.loads(mpath.read_text(encoding="utf-8")), sha256_file(mpath)


def load_reference_table(ref_dir: Path, table: str, required: bool = True) -> Rows | None:
    p = ref_dir / f"{table}.csv"
    if not p.is_file():
        if required:
            raise ReferenceMissing(f"{p} does not exist")
        return None
    return read_csv(p)
