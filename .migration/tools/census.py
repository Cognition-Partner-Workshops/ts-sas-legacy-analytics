#!/usr/bin/env python3
"""Mechanical, re-runnable census and lightweight lineage extractor for the SAS estate."""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Iterable


REPO = Path(__file__).resolve().parents[2]
OUT_DIR = Path(__file__).resolve().parent
JSON_PATH = OUT_DIR / "census.json"
SUMMARY_PATH = OUT_DIR / "census_summary.md"
EXCLUDED_DIRS = {".git", "docs", ".migration"}
SOURCE_DIRS = ("Config", "Formats", "Macro", "Programs", "BatchJobs")
BUILTIN_MACROS = {
    "let", "put", "if", "then", "else", "do", "end", "eval", "sysfunc",
    "str", "nrstr", "upcase", "lowcase", "scan", "substr", "sysevalf",
    "global", "local", "macro", "mend", "symdel", "sysexec", "bquote",
    "nrbquote", "quote", "index", "length", "superq", "unquote", "trim",
    "left", "cmpres", "qsysfunc", "qscan", "qupcase", "datatyp", "verify",
    "return", "goto", "abort", "syscall", "sysget", "sysrput", "syslput",
    "window", "display", "input", "qsubstr", "klength", "kcmpres",
}
MACRO_CALL_RE = re.compile(r"%([A-Za-z_][A-Za-z0-9_]*)\s*(?=[(;])")
MACRO_DEF_RE = re.compile(r"%macro\s+([A-Za-z_][A-Za-z0-9_]*)\b", re.I)
TWO_LEVEL_RE = re.compile(r"\b([A-Za-z_][A-Za-z0-9_]*)\.([A-Za-z_][A-Za-z0-9_]*)\b")
SINGLE_NAME_RE = re.compile(r"\b([A-Za-z_][A-Za-z0-9_]*)\b")


def relpath(path: Path) -> str:
    return path.relative_to(REPO).as_posix()


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def iter_files() -> list[Path]:
    files: list[Path] = []
    for root, dirs, names in os.walk(REPO):
        dirs[:] = sorted(d for d in dirs if d not in EXCLUDED_DIRS)
        for name in sorted(names):
            path = Path(root) / name
            if not path.is_symlink() and path.is_file():
                files.append(path)
    return sorted(files, key=relpath)


def mask_sas_comments(text: str) -> str:
    """Remove block and statement comments while retaining line positions."""
    chars = list(text)
    i = 0
    n = len(chars)
    in_string: str | None = None
    while i < n:
        if in_string:
            if text[i] == in_string:
                if i + 1 < n and text[i + 1] == in_string:
                    i += 2
                    continue
                in_string = None
            i += 1
            continue
        if text[i] in "'\"":
            in_string = text[i]
            i += 1
            continue
        if i + 1 < n and text[i:i + 2] == "/*":
            end_marker = text.find("*/", i + 2)
            end = n if end_marker < 0 else end_marker + 2
            for j in range(i, end):
                if text[j] != "\n":
                    chars[j] = " "
            i = end
            continue
        # SAS statement comments begin with * (or %*) and end at a semicolon.
        line_prefix = text[text.rfind("\n", 0, i) + 1:i]
        line_start = not line_prefix.strip()
        if line_start and text[i] == "*":
            end = text.find(";", i)
            end = n if end < 0 else end + 1
            for j in range(i, end):
                if text[j] != "\n":
                    chars[j] = " "
            i = end
            continue
        if line_start and text[i:i + 2] == "%*":
            end = text.find(";", i)
            end = n if end < 0 else end + 1
            for j in range(i, end):
                if text[j] != "\n":
                    chars[j] = " "
            i = end
            continue
        i += 1
    return "".join(chars)


def line_number(text: str, offset: int) -> int:
    return text.count("\n", 0, offset) + 1


def split_top_level(value: str) -> list[str]:
    parts: list[str] = []
    start = 0
    depth = 0
    quote: str | None = None
    i = 0
    while i < len(value):
        ch = value[i]
        if quote:
            if ch == quote:
                if i + 1 < len(value) and value[i + 1] == quote:
                    i += 2
                    continue
                quote = None
        elif ch in "'\"":
            quote = ch
        elif ch == "(":
            depth += 1
        elif ch == ")":
            depth = max(0, depth - 1)
        elif ch == "," and depth == 0:
            parts.append(value[start:i].strip())
            start = i + 1
        i += 1
    parts.append(value[start:].strip())
    return parts


def macro_invocations(text: str, names: Iterable[str] | None = None) -> list[dict]:
    wanted = {name.lower() for name in names} if names else None
    result: list[dict] = []
    for match in re.finditer(r"%([A-Za-z_][A-Za-z0-9_]*)\s*([(;])", text):
        name = match.group(1)
        lower = name.lower()
        if lower in BUILTIN_MACROS or (wanted is not None and lower not in wanted):
            continue
        if lower in {"macro", "mend"}:
            continue
        line = line_number(text, match.start())
        delimiter = match.group(2)
        args = ""
        if delimiter == "(":
            start = match.end()
            depth = 1
            quote: str | None = None
            i = start
            while i < len(text) and depth:
                ch = text[i]
                if quote:
                    if ch == quote:
                        if i + 1 < len(text) and text[i + 1] == quote:
                            i += 2
                            continue
                        quote = None
                elif ch in "'\"":
                    quote = ch
                elif ch == "(":
                    depth += 1
                elif ch == ")":
                    depth -= 1
                i += 1
            args = text[start:i - 1].strip() if depth == 0 else text[start:].strip()
        result.append({"name": name.lower(), "line": line, "arguments": args})
    return result


def extract_refs(text: str) -> dict:
    """Extract static two-level refs and unqualified WORK dataset refs."""
    cleaned = mask_sas_comments(text)
    reads: set[str] = set()
    writes: set[str] = set()
    work_reads: set[str] = set()
    work_writes: set[str] = set()

    def add_ref(raw: str, target: set[str], work_target: set[str]) -> None:
        token = raw.strip().strip(";,()")
        token = token.split("/", 1)[0].strip()
        if not token or token.startswith("&") or token.startswith(":"):
            return
        two = re.fullmatch(r"([A-Za-z_][A-Za-z0-9_]*)\.([A-Za-z_][A-Za-z0-9_]*)", token)
        if two:
            lib, member = two.groups()
            if lib.lower() == "work":
                work_target.add(member.upper())
            else:
                target.add(f"{lib.upper()}.{member.upper()}")
            return
        if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", token):
            work_target.add(token.upper())

    # Dataset references following read/write keywords. A keyword may be
    # followed by multiple dataset names (SET/MERGE) or SQL joins.
    read_keyword = re.compile(
        r"\b(set|merge|from|join|update|modify)\s+", re.I
    )

    def add_leading_dataset(
        match: re.Match[str], target: set[str], work_target: set[str]
    ) -> None:
        tail = cleaned[match.end():match.end() + 1000]
        keyword = match.group(1).lower()
        if keyword in {"set", "merge"}:
            tail = tail.split(";", 1)[0]
            tail = re.sub(r"\([^()]*\)", " ", tail)
            tail = re.sub(
                r"\b(?:key|point|nobs|indsname|open)\s*=\s*\S+", " ", tail, flags=re.I
            )
            for token in re.finditer(
                r"\b([A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)?)\b",
                tail,
            ):
                add_ref(token.group(1), target, work_target)
        else:
            token = re.match(
                r"\s*([A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)?)", tail
            )
            if token:
                add_ref(token.group(1), target, work_target)

    for match in read_keyword.finditer(cleaned):
        add_leading_dataset(match, reads, work_reads)

    # DATA= options identify an input dataset, while PROC EXPORT's DATA=
    # is additionally recorded as a write/export source below.
    for match in re.finditer(
        r"\bdata\s*=\s*([A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)?)",
        cleaned,
        re.I,
    ):
        add_ref(match.group(1), reads, work_reads)

    # DATA step targets (including DATA view= syntax) are writes.
    for match in re.finditer(
        r"(?:^|;)[ \t]*data\s+(?![=])\s*"
        r"([A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)?)",
        cleaned,
        re.I | re.M,
    ):
        add_ref(match.group(1), writes, work_writes)

    for match in re.finditer(
        r"\b(?:out|base)\s*=\s*([A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)?)",
        cleaned,
        re.I,
    ):
        add_ref(match.group(1), writes, work_writes)
    for match in re.finditer(
        r"\b(?:create\s+(?:table|view)|insert\s+into)\s+"
        r"([A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)?)",
        cleaned,
        re.I,
    ):
        add_ref(match.group(1), writes, work_writes)

    # Remove WORK from lineage lists by design.
    return {
        "reads": sorted(reads),
        "writes": sorted(writes),
        "work_reads": sorted(work_reads),
        "work_writes": sorted(work_writes),
    }


def parse_sas(path: Path) -> dict:
    text = read_text(path)
    cleaned = mask_sas_comments(text)
    lines = text.count("\n") + (1 if text and not text.endswith("\n") else 0)
    proc_counts = Counter(
        match.group(1).lower()
        for match in re.finditer(r"\bproc\s+([A-Za-z_][A-Za-z0-9_]*)\b", cleaned, re.I)
    )
    macro_defs = [
        {"name": match.group(1).lower(), "line": line_number(cleaned, match.start())}
        for match in MACRO_DEF_RE.finditer(cleaned)
    ]
    includes = []
    for match in re.finditer(r"%include\s+(.+?);", cleaned, re.I | re.S):
        target = match.group(1).strip()
        target = re.sub(r"\s*/\s*source2\s*$", "", target, flags=re.I).strip()
        includes.append({"target": target, "line": line_number(cleaned, match.start())})
    calls = macro_invocations(cleaned)
    refs = extract_refs(text)
    export_files = []
    # PROC EXPORT's DATA= is both a consumed dataset and an export edge.
    for match in re.finditer(
        r"\bproc\s+export\b(.*?)(?:\brun\s*;|\Z)", cleaned, re.I | re.S
    ):
        body = match.group(1)
        data_match = re.search(
            r"\bdata\s*=\s*([A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)?)",
            body,
            re.I,
        )
        outfile_match = re.search(r"\boutfile\s*=\s*([^\s;]+)", body, re.I)
        if data_match:
            add_ref(data_match.group(1), refs["reads"], refs["work_reads"])
            add_ref(data_match.group(1), refs["writes"], refs["work_writes"])
        if data_match or outfile_match:
            export_files.append(
                {
                    "line": line_number(cleaned, match.start()),
                    "data": data_match.group(1) if data_match else "",
                    "outfile": outfile_match.group(1) if outfile_match else "",
                }
            )
    consumers = [
        {"call": call["name"], "arguments": call["arguments"], "line": call["line"]}
        for call in calls
        if call["name"] in {"export_xlsx", "sendmail"}
    ]
    return {
        "path": relpath(path),
        "lines": lines,
        "proc_counts": dict(sorted(proc_counts.items())),
        "data_steps": len(
            re.findall(r"(?:^|;)[ \t]*data\s+(?![=])", cleaned, re.I | re.M)
        ),
        "macro_definitions": macro_defs,
        "include_targets": includes,
        "macro_calls": calls,
        "macro_call_counts": dict(sorted(Counter(c["name"] for c in calls).items())),
        "reads": refs["reads"],
        "writes": refs["writes"],
        "work_reads": refs["work_reads"],
        "work_writes": refs["work_writes"],
        "consumer_edges": consumers,
        "proc_export_files": export_files,
    }


def parse_file_census(files: list[Path]) -> tuple[list[dict], dict[str, dict]]:
    records: list[dict] = []
    sas_records: dict[str, dict] = {}
    for path in files:
        rel = relpath(path)
        suffix = path.suffix.lower()
        record = {
            "path": rel,
            "extension": suffix[1:] if suffix else "",
            "bytes": path.stat().st_size,
        }
        if suffix == ".sas":
            parsed = parse_sas(path)
            record["lines"] = parsed["lines"]
            sas_records[rel] = parsed
        records.append(record)
    return records, sas_records


def top_level_counts(files: list[dict]) -> list[dict]:
    grouped: dict[str, Counter] = defaultdict(Counter)
    for record in files:
        parts = record["path"].split("/")
        top = parts[0] if len(parts) > 1 else "."
        grouped[top]["files"] += 1
        grouped[top]["bytes"] += record["bytes"]
        if record["extension"] == "sas":
            grouped[top]["sas_files"] += 1
    return [
        {
            "top_level": top,
            "files": values["files"],
            "bytes": values["bytes"],
            "sas_files": values["sas_files"],
        }
        for top, values in sorted(grouped.items())
    ]


def directory_groups(files: list[dict]) -> list[dict]:
    grouped: dict[str, Counter] = defaultdict(Counter)
    for record in files:
        parts = record["path"].split("/")
        if len(parts) == 1:
            group = parts[0]
        elif parts[0] == "Programs":
            group = "/".join(parts[:2])
        else:
            group = parts[0]
        grouped[group]["files"] += 1
        grouped[group]["bytes"] += record["bytes"]
        if record["extension"] == "sas":
            grouped[group]["sas_files"] += 1
    return [
        {
            "group": group,
            "files": values["files"],
            "bytes": values["bytes"],
            "sas_files": values["sas_files"],
        }
        for group, values in sorted(grouped.items())
    ]


def parse_batch_steps(path: Path) -> list[dict]:
    text = mask_sas_comments(read_text(path))
    result = []
    for call in macro_invocations(text, {"run_step"}):
        args = split_top_level(call["arguments"])
        result.append(
            {
                "line": call["line"],
                "step_number": args[0] if args else "",
                "step_name": args[1] if len(args) > 1 else "",
                "program": args[2] if len(args) > 2 else "",
                "arguments": args,
            }
        )
    return result


def parse_formats(path: Path) -> list[dict]:
    text = mask_sas_comments(read_text(path))
    return [
        {"path": relpath(path), "name": match.group(1).lstrip("$").upper(),
         "line": line_number(text, match.start())}
        for match in re.finditer(r"\bvalue\s+\$?([A-Za-z_][A-Za-z0-9_]*)\b", text, re.I)
    ]


def macro_inventory(sas_records: dict[str, dict]) -> tuple[list[dict], list[dict]]:
    primary_by_file: dict[str, tuple[str, int]] = {}
    for path, record in sas_records.items():
        if not path.startswith("Macro/") or not record["macro_definitions"]:
            continue
        stem = Path(path).stem.lstrip("@").lower()
        selected = next(
            (
                definition
                for definition in record["macro_definitions"]
                if definition["name"].lower() == stem
            ),
            record["macro_definitions"][0],
        )
        primary_by_file[path] = (selected["name"], selected["line"])

    definitions: dict[str, list[tuple[str, int]]] = defaultdict(list)
    for path, (name, line) in primary_by_file.items():
        definitions[name].append((path, line))

    call_sites: dict[str, list[dict]] = defaultdict(list)
    for path, record in sas_records.items():
        if not (
            path.startswith("Programs/")
            or path.startswith("BatchJobs/")
            or path.startswith("Config/")
            or path.startswith("Macro/")
        ):
            continue
        for call in record["macro_calls"]:
            if call["name"] in definitions:
                call_sites[call["name"]].append(
                    {"file": path, "line": call["line"], "arguments": call["arguments"]}
                )

    inventory = []
    for name, defs in sorted(definitions.items()):
        definition_path, definition_line = defs[0]
        sites = [
            site for site in call_sites.get(name, [])
            if site["file"] != definition_path
        ]
        external_sites = [
            site for site in sites
            if site["file"].startswith(("Programs/", "BatchJobs/", "Config/"))
        ]
        other_macro_sites = [
            site for site in sites
            if site["file"].startswith("Macro/") and site["file"] != definition_path
        ]
        inventory.append(
            {
                "is_macro": True,
                "name": name,
                "file": definition_path,
                "definition_line": definition_line,
                "line_count": sas_records[definition_path]["lines"],
                "call_count": len(sites),
                "external_call_count": len(external_sites),
                "called_by_other_macros": bool(other_macro_sites),
                "call_sites": sites,
                "call_files": sorted({site["file"] for site in sites}),
            }
        )
    for path, record in sorted(sas_records.items()):
        if path.startswith("Macro/") and not record["macro_definitions"]:
            inventory.append(
                {
                    "is_macro": False,
                    "name": "(support file; no macro definition)",
                    "file": path,
                    "definition_line": None,
                    "line_count": record["lines"],
                    "call_count": 0,
                    "external_call_count": 0,
                    "called_by_other_macros": False,
                    "call_sites": [],
                    "call_files": [],
                }
            )
    odd_files = [
        path for path in sorted(p for p in sas_records if p.startswith("Macro/"))
        if not sas_records[path]["macro_definitions"]
    ]
    return inventory, [{"path": path, "reason": "no macro definition"} for path in odd_files]


def cross_references(files: list[Path]) -> list[dict]:
    targets: list[Path] = []
    for path in files:
        rel = relpath(path)
        if (
            rel.startswith(("AMO/", "EGProjects/", "Logs/", "Presentations/"))
            or rel == "Programs/Parent-Child-Index.sas"
            or re.fullmatch(r"Data/[^/]+\.(sas|py|sh)", rel, re.I)
            or re.fullmatch(r"Data/local/[^/]+\.sas", rel, re.I)
        ):
            targets.append(path)
    source_files = [
        path for path in files
        if path.suffix.lower() == ".sas"
        and path.relative_to(REPO).parts[0] in SOURCE_DIRS
    ]
    result = []
    for target in targets:
        target_rel = relpath(target)
        name = target.name.lower()
        stem = target.stem.lower()
        cites: list[str] = []
        for source in source_files:
            source_rel = relpath(source)
            text = read_text(source)
            for number, line in enumerate(text.splitlines(), 1):
                lowered = line.lower()
                if name in lowered or stem in lowered:
                    cites.append(f"{source_rel}:{number}")
        result.append(
            {
                "target": target_rel,
                "referenced": bool(cites),
                "cites": sorted(set(cites)),
            }
        )
    return result


def autoexec_extract(path: Path) -> dict:
    text = mask_sas_comments(read_text(path))
    libnames = []
    for match in re.finditer(
        r"\blibname\s+([A-Za-z_][A-Za-z0-9_]*)\s+(.+?);", text, re.I | re.S
    ):
        statement = " ".join(match.group(0).split())
        remainder = match.group(2).strip()
        first = re.match(r"([A-Za-z_][A-Za-z0-9_]*|\"[^\"]*\"|'[^']*')", remainder)
        first_value = first.group(1) if first else ""
        engine = "BASE" if first_value.startswith(('"', "'")) else first_value.upper()
        quoted = re.search(r'(["\'])(.*?)\1', remainder, re.S)
        path_value = quoted.group(2) if quoted else ""
        if not path_value and engine not in {"BASE", ""}:
            path_value = remainder
        libnames.append(
            {
                "libref": match.group(1).upper(),
                "engine": engine,
                "path": path_value,
                "line": line_number(text, match.start()),
                "statement": statement,
            }
        )
    lets = [
        {"name": match.group(1).upper(), "line": line_number(text, match.start())}
        for match in re.finditer(
            r"%let\s+([A-Za-z_][A-Za-z0-9_]*)\s*=", text, re.I
        )
    ]
    return {"path": relpath(path), "libnames": libnames, "macro_variables": lets}


def graphviz_check() -> dict:
    dot = shutil.which("dot")
    if dot:
        version = subprocess.run(
            [dot, "-V"], capture_output=True, text=True, check=False
        )
        return {
            "installed": True,
            "which": dot,
            "version": (version.stderr or version.stdout).strip(),
            "install_attempted": False,
            "install_result": "already installed",
        }
    command = ["sudo", "-n", "apt-get", "install", "-y", "graphviz"]
    attempt = subprocess.run(command, capture_output=True, text=True, check=False)
    dot_after = shutil.which("dot")
    return {
        "installed": bool(dot_after),
        "which": dot_after,
        "version": "",
        "install_attempted": True,
        "install_command": "sudo -n apt-get install -y graphviz",
        "install_returncode": attempt.returncode,
        "install_stdout": attempt.stdout[-2000:],
        "install_stderr": attempt.stderr[-2000:],
        "install_result": "installed" if dot_after else "failed; render DAG another way",
    }


def markdown_escape(value: object) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ")


def table(headers: list[str], rows: Iterable[Iterable[object]]) -> str:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    lines.extend(
        "| " + " | ".join(markdown_escape(cell) for cell in row) + " |"
        for row in rows
    )
    return "\n".join(lines)


def summary_markdown(census: dict) -> str:
    format_counts = {
        Path(row["path"]).name: row["value_count"]
        for row in census["format_summary"]
    }
    lines = [
        "# SAS estate census",
        "",
        f"Repository: `{census['repository']}`",
        (
            f"Macro inventory: {census['macro_summary']['definition_count']} "
            f"entries across {census['macro_summary']['macro_file_count']} "
            f"Macro/ files; {census['macro_summary']['all_definition_count']} "
            f"total `%macro` statements were found "
            f"({census['macro_summary']['actual_definition_count']} primary "
            "macro definitions plus support files)."
        ),
        (
            "Format inventory: "
            + ", ".join(
                f"{Path(row['path']).name}={row['value_count']}"
                for row in census["format_summary"]
            )
        ),
        (
            "Sanity expectations vs observed: "
            f"92 macro entries / {census['macro_summary']['definition_count']} observed; "
            f"banking formats 10 / {format_counts.get('banking_formats.sas', 0)} "
            "observed; "
            f"insurance formats 6 / {format_counts.get('insurance_formats.sas', 0)} "
            "observed."
        ),
        "",
        "## Per-directory file table",
        "",
        table(
            ["Directory group", "Files", "SAS files", "Bytes"],
            (
                (row["group"], row["files"], row["sas_files"], row["bytes"])
                for row in census["directory_groups"]
            ),
        ),
        "",
        "## Per-SAS-file table",
        "",
        table(
            ["Path", "Lines", "# proc", "Top procs", "# data steps", "Reads", "Writes"],
            (
                (
                    row["path"],
                    row["lines"],
                    sum(row["proc_counts"].values()),
                    ", ".join(
                        f"{name} ({count})"
                        for name, count in sorted(
                            row["proc_counts"].items(),
                            key=lambda item: (-item[1], item[0]),
                        )[:5]
                    ) or "—",
                    row["data_steps"],
                    ", ".join(row["reads"]) or "—",
                    ", ".join(row["writes"]) or "—",
                )
                for row in sorted(census["sas_files"], key=lambda item: item["path"])
            ),
        ),
        "",
        "## Macro usage",
        "",
        table(
            ["Macro", "Definition", "Lines", "Calls", "Call files"],
            (
                (
                    row["name"],
                    f"{row['file']}:{row['definition_line']}",
                    row["line_count"],
                    row["call_count"],
                    ", ".join(row["call_files"]) or "—",
                )
                for row in census["macros"]
            ),
        ),
        "",
        "## Format list",
        "",
        table(
            ["File", "Format", "Line"],
            ((row["path"], row["name"], row["line"]) for row in census["formats"]),
        ),
        "",
        "## Batch run_step order",
        "",
    ]
    for batch in census["batch_run_steps"]:
        lines.extend(
            [
                f"### {batch['path']}",
                "",
                table(
                    ["Order", "Step", "Step name", "Program", "Line"],
                    (
                        (
                            order,
                            step["step_number"],
                            step["step_name"],
                            step["program"],
                            step["line"],
                        )
                        for order, step in enumerate(batch["steps"], 1)
                    ),
                ),
                "",
            ]
        )
    lines.extend(
        [
            "## Libnames",
            "",
            table(
                ["File", "Libref", "Engine", "Path", "Line"],
                (
                    (
                        row["path"],
                        lib["libref"],
                        lib["engine"],
                        lib["path"],
                        lib["line"],
                    )
                    for row in census["autoexecs"]
                    for lib in row["libnames"]
                ),
            ),
            "",
            "## Autoexec `%let` variables",
            "",
            table(
                ["File", "Variable", "Line"],
                (
                    (row["path"], var["name"], var["line"])
                    for row in census["autoexecs"]
                    for var in row["macro_variables"]
                ),
            ),
            "",
            "## Step-3 cross-reference table",
            "",
            table(
                ["Target", "Referenced", "Cites"],
                (
                    (
                        row["target"],
                        "yes" if row["referenced"] else "no",
                        ", ".join(row["cites"]) or "—",
                    )
                    for row in census["cross_references"]
                ),
            ),
            "",
            "## Unused macros",
            "",
            "Macros with zero calls from `Programs/`, `BatchJobs/`, and `Config/`; "
            "the final column identifies calls from other macro files.",
            "",
            table(
                ["Macro", "Definition", "Called by other macros"],
                (
                    (
                        row["name"],
                        row["file"],
                        "yes" if row["called_by_other_macros"] else "no",
                    )
                    for row in census["macros"]
                    if row.get("is_macro", True) and row["external_call_count"] == 0
                ),
            ),
            "",
            "## Graphviz check",
            "",
            f"- Result: `{census['graphviz']['install_result']}`",
            f"- `which dot`: `{census['graphviz'].get('which') or 'not found'}`",
        ]
    )
    return "\n".join(lines) + "\n"


def build_census() -> dict:
    files = iter_files()
    file_records, sas_records = parse_file_census(files)
    formats = [
        format_record
        for path in files
        if relpath(path).startswith("Formats/") and path.suffix.lower() == ".sas"
        for format_record in parse_formats(path)
    ]
    batches = [
        {"path": relpath(path), "steps": parse_batch_steps(path)}
        for path in files
        if relpath(path).startswith("BatchJobs/") and path.suffix.lower() == ".sas"
    ]
    macros, macro_odd_files = macro_inventory(sas_records)
    autoexecs = [
        autoexec_extract(path)
        for path in files
        if relpath(path) in {"Config/autoexec.sas", "Config/autoexec_local.sas"}
    ]
    sas_files = [sas_records[path] for path in sorted(sas_records)]
    for record in sas_files:
        record["macro_calls"] = sorted(
            record["macro_calls"], key=lambda call: (call["line"], call["name"])
        )
    return {
        "repository": str(REPO),
        "excluded_directories": sorted(EXCLUDED_DIRS),
        "files": file_records,
        "directories": top_level_counts(file_records),
        "directory_groups": directory_groups(file_records),
        "sas_files": sas_files,
        "macros": sorted(macros, key=lambda row: (-row["call_count"], row["name"])),
        "macro_summary": {
            "definition_count": len(macros),
            "entry_count": len(macros),
            "actual_definition_count": sum(
                1 for row in macros if row.get("is_macro", True)
            ),
            "all_definition_count": sum(
                len(record["macro_definitions"])
                for path, record in sas_records.items()
                if path.startswith("Macro/")
            ),
            "macro_sas_file_count": sum(
                1 for path in sas_records if path.startswith("Macro/")
            ),
            "macro_file_count": sum(
                1 for path in files if relpath(path).startswith("Macro/")
            ),
            "odd_files": macro_odd_files,
            "non_sas_files": [
                record["path"]
                for record in file_records
                if record["path"].startswith("Macro/") and record["extension"] != "sas"
            ],
        },
        "formats": sorted(formats, key=lambda row: (row["path"], row["line"])),
        "format_summary": [
            {
                "path": path,
                "value_count": sum(1 for row in formats if row["path"] == path),
            }
            for path in sorted({row["path"] for row in formats})
        ],
        "requested_sanity": {
            "macro_definition_count": {
                "expected": 92,
                "observed_entries": len(macros),
                "observed_actual_definitions": sum(
                    1 for row in macros if row.get("is_macro", True)
                ),
            },
            "format_value_counts": {
                "expected": {"banking_formats.sas": 10, "insurance_formats.sas": 6},
                "observed": {
                    Path(row["path"]).name: row["value_count"]
                    for row in [
                        {
                            "path": path,
                            "value_count": sum(
                                1 for item in formats if item["path"] == path
                            ),
                        }
                        for path in sorted({item["path"] for item in formats})
                    ]
                },
            },
            "run_steps": {
                Path(row["path"]).stem: len(row["steps"]) for row in batches
            },
        },
        "batch_run_steps": sorted(batches, key=lambda row: row["path"]),
        "autoexecs": sorted(autoexecs, key=lambda row: row["path"]),
        "cross_references": cross_references(files),
        "graphviz": graphviz_check(),
    }


def main() -> int:
    census = build_census()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    JSON_PATH.write_text(json.dumps(census, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    SUMMARY_PATH.write_text(summary_markdown(census), encoding="utf-8")
    print(f"Wrote {JSON_PATH}")
    print(f"Wrote {SUMMARY_PATH}")
    print(
        "Sanity: macro_entries={}; actual_macro_definitions={}; "
        "total_macro_statements={}; macro_files={}; "
        "formats={}; banking run_steps={}; insurance run_steps={}".format(
            census["macro_summary"]["definition_count"],
            census["macro_summary"]["actual_definition_count"],
            census["macro_summary"]["all_definition_count"],
            census["macro_summary"]["macro_file_count"],
            len(census["formats"]),
            next(
                (
                    len(row["steps"])
                    for row in census["batch_run_steps"]
                    if row["path"].endswith("run_daily_banking.sas")
                ),
                "?",
            ),
            next(
                (
                    len(row["steps"])
                    for row in census["batch_run_steps"]
                    if row["path"].endswith("run_daily_insurance.sas")
                ),
                "?",
            ),
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
