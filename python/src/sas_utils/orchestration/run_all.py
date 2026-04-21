"""
Run All orchestration utility.

Migrated from: Macro/RunAll.sas
Original author: Scott Bass (01MAY2010)

Runs Python programs/functions asynchronously and multi-threaded,
honoring job dependencies via group ordering.
"""

from __future__ import annotations

import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Optional, Sequence, Union


@dataclass
class ProgramResult:
    """Result of a single program execution."""
    program: str
    return_code: int
    stdout: str = ""
    stderr: str = ""

    @property
    def success(self) -> bool:
        return self.return_code == 0

    @property
    def status(self) -> str:
        if self.return_code == 0:
            return "Ended Successfully"
        elif self.return_code == 1:
            return "Ended With Warnings"
        else:
            return "Ended With Errors"


@dataclass
class ProgramSpec:
    """Specification for a program to run."""
    program: str
    group: int = 0

    def __post_init__(self) -> None:
        self.program = str(self.program)


def run_all(
    programs: Sequence[Union[str, ProgramSpec, dict]],
    max_threads: int = 4,
    abort_on_error: bool = True,
    runner: Optional[Callable[[str], ProgramResult]] = None,
) -> list[ProgramResult]:
    """
    Run programs multi-threaded, honoring group-based dependencies.

    Programs in the same group run in parallel. Groups run sequentially
    in ascending order. If ``abort_on_error`` is True, execution stops
    when any program in a group fails.

    Parameters
    ----------
    programs : list
        List of program specifications. Each can be:
        - A string (program path, group defaults to 0)
        - A ProgramSpec object
        - A dict with ``"program"`` and optional ``"group"`` keys
    max_threads : int
        Maximum concurrent threads. Default 4.
    abort_on_error : bool
        If True, abort on first group error. Default True.
    runner : callable, optional
        Custom function to run a program. Takes a program path string,
        returns a ProgramResult. Default uses subprocess.

    Returns
    -------
    list of ProgramResult
        Results for each program that was run.
    """
    specs = _normalize_specs(programs)

    # Group programs by their group number
    groups: dict[int, list[ProgramSpec]] = {}
    for spec in specs:
        groups.setdefault(spec.group, []).append(spec)

    if runner is None:
        runner = _default_runner

    all_results: list[ProgramResult] = []

    # Execute groups sequentially
    for group_num in sorted(groups.keys()):
        group_specs = groups[group_num]
        group_results = _run_group(group_specs, max_threads, runner)
        all_results.extend(group_results)

        # Check for errors
        if abort_on_error:
            if any(not r.success for r in group_results):
                break

    return all_results


def _normalize_specs(programs: Sequence) -> list[ProgramSpec]:
    """Normalize input to list of ProgramSpec."""
    specs = []
    for p in programs:
        if isinstance(p, ProgramSpec):
            specs.append(p)
        elif isinstance(p, dict):
            specs.append(ProgramSpec(
                program=p["program"],
                group=p.get("group", 0),
            ))
        else:
            specs.append(ProgramSpec(program=str(p)))
    return specs


def _run_group(
    specs: list[ProgramSpec],
    max_threads: int,
    runner: Callable,
) -> list[ProgramResult]:
    """Run a group of programs in parallel."""
    results = []

    with ThreadPoolExecutor(max_workers=min(max_threads, len(specs))) as executor:
        futures = {
            executor.submit(runner, spec.program): spec
            for spec in specs
        }
        for future in as_completed(futures):
            try:
                result = future.result()
            except Exception as e:
                spec = futures[future]
                result = ProgramResult(
                    program=spec.program,
                    return_code=-1,
                    stderr=str(e),
                )
            results.append(result)

    return results


def _default_runner(program: str) -> ProgramResult:
    """Default program runner using subprocess."""
    try:
        proc = subprocess.run(
            [sys.executable, program],
            capture_output=True,
            text=True,
            timeout=3600,
        )
        return ProgramResult(
            program=program,
            return_code=proc.returncode,
            stdout=proc.stdout,
            stderr=proc.stderr,
        )
    except subprocess.TimeoutExpired:
        return ProgramResult(
            program=program,
            return_code=-1,
            stderr="Program timed out after 3600 seconds",
        )
    except FileNotFoundError:
        return ProgramResult(
            program=program,
            return_code=-1,
            stderr=f"Program {program!r} not found",
        )
