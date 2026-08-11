"""
Tests for sas_utils.orchestration.run_all

Derived from Macro/RunAll.sas Usage block.
"""

import pytest

from sas_utils.orchestration.run_all import ProgramResult, ProgramSpec, run_all


# ====================================================================
# Test: basic execution with mock runner
# ====================================================================
class TestRunAll:
    def test_single_program(self):
        def mock_runner(program):
            return ProgramResult(program=program, return_code=0)

        results = run_all(["test.py"], runner=mock_runner)
        assert len(results) == 1
        assert results[0].success is True

    def test_multiple_programs_same_group(self):
        executed = []

        def mock_runner(program):
            executed.append(program)
            return ProgramResult(program=program, return_code=0)

        results = run_all(["a.py", "b.py", "c.py"], runner=mock_runner)
        assert len(results) == 3
        assert set(executed) == {"a.py", "b.py", "c.py"}


# ====================================================================
# Test: group-based dependencies
# ====================================================================
class TestGroupDependencies:
    def test_sequential_groups(self):
        order = []

        def mock_runner(program):
            order.append(program)
            return ProgramResult(program=program, return_code=0)

        programs = [
            {"program": "first.py", "group": 1},
            {"program": "second.py", "group": 2},
            {"program": "third.py", "group": 3},
        ]
        results = run_all(programs, max_threads=1, runner=mock_runner)
        assert len(results) == 3
        assert order == ["first.py", "second.py", "third.py"]


# ====================================================================
# Test: abort on error
# ====================================================================
class TestAbortOnError:
    def test_abort_stops_processing(self):
        def mock_runner(program):
            if program == "fail.py":
                return ProgramResult(program=program, return_code=2)
            return ProgramResult(program=program, return_code=0)

        programs = [
            {"program": "fail.py", "group": 1},
            {"program": "should_not_run.py", "group": 2},
        ]
        results = run_all(programs, abort_on_error=True, runner=mock_runner)
        programs_run = {r.program for r in results}
        assert "fail.py" in programs_run
        assert "should_not_run.py" not in programs_run

    def test_no_abort_continues(self):
        def mock_runner(program):
            if program == "fail.py":
                return ProgramResult(program=program, return_code=2)
            return ProgramResult(program=program, return_code=0)

        programs = [
            {"program": "fail.py", "group": 1},
            {"program": "should_run.py", "group": 2},
        ]
        results = run_all(programs, abort_on_error=False, runner=mock_runner)
        programs_run = {r.program for r in results}
        assert "should_run.py" in programs_run


# ====================================================================
# Test: ProgramResult properties
# ====================================================================
class TestProgramResult:
    def test_success_property(self):
        r = ProgramResult(program="test.py", return_code=0)
        assert r.success is True
        assert r.status == "Ended Successfully"

    def test_failure_property(self):
        r = ProgramResult(program="test.py", return_code=2)
        assert r.success is False
        assert r.status == "Ended With Errors"

    def test_warning_status(self):
        r = ProgramResult(program="test.py", return_code=1)
        assert r.status == "Ended With Warnings"
