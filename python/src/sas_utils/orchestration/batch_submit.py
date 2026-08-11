"""
Batch submit utility.

Migrated from: Macro/batch_submit.sas
Original author: Scott Bass

Submits a list of Python scripts in batch mode via subprocess.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import Optional, Sequence, Union

from sas_utils.orchestration.run_all import ProgramResult


def batch_submit(
    programs: Sequence[Union[str, Path]],
    python: Optional[str] = None,
    timeout: int = 3600,
) -> list[ProgramResult]:
    """
    Submit a list of Python programs sequentially.

    Parameters
    ----------
    programs : list of str or Path
        List of Python script paths to run.
    python : str, optional
        Python interpreter path. Default: ``sys.executable``.
    timeout : int
        Per-program timeout in seconds. Default 3600.

    Returns
    -------
    list of ProgramResult
        Results for each program.
    """
    if python is None:
        python = sys.executable

    results = []
    for program in programs:
        program_str = str(program)
        try:
            proc = subprocess.run(
                [python, program_str],
                capture_output=True,
                text=True,
                timeout=timeout,
            )
            results.append(ProgramResult(
                program=program_str,
                return_code=proc.returncode,
                stdout=proc.stdout,
                stderr=proc.stderr,
            ))
        except subprocess.TimeoutExpired:
            results.append(ProgramResult(
                program=program_str,
                return_code=-1,
                stderr=f"Timed out after {timeout} seconds",
            ))
        except FileNotFoundError:
            results.append(ProgramResult(
                program=program_str,
                return_code=-1,
                stderr=f"Program {program_str!r} not found",
            ))

    return results
