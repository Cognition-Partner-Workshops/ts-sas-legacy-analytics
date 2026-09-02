import json
import subprocess
import sys
import types
from pathlib import Path

import pytest

from recon import run_recon
from recon.warehouse import Warehouse, WarehouseError

REPO = Path(__file__).parents[2]
FIXTURES = Path(__file__).parent / "fixtures"


def _script_args(out: Path, target: str = "target") -> list[str]:
    return [
        sys.executable,
        "databricks/recon/run_recon.py",
        "--unit",
        "U3",
        "--mode",
        "fixture",
        "--business-date",
        "2024-01-31",
        "--out",
        str(out),
        "--reference-dir",
        str(FIXTURES / "reference"),
        "--target-dir",
        str(FIXTURES / target),
    ]


def test_default_reference_points_to_manifest():
    assert run_recon.DEFAULT_REF.is_dir()
    assert (run_recon.DEFAULT_REF / "manifest.json").is_file()


def test_script_fixture_pass_writes_recon_json(tmp_path):
    result = subprocess.run(
        _script_args(tmp_path),
        cwd=REPO,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    report = json.loads((tmp_path / "recon.json").read_text())
    assert report["overall"] == "PASS"


def test_script_fixture_fail_returns_one(tmp_path):
    result = subprocess.run(
        _script_args(tmp_path, target="target_bad"),
        cwd=REPO,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 1, result.stderr
    report = json.loads((tmp_path / "recon.json").read_text())
    assert report["overall"] == "FAIL"


def test_output_dir_falls_back_to_unique_writable_dir(tmp_path, monkeypatch):
    def fail_mkdir(self, *args, **kwargs):
        raise PermissionError("read-only")

    monkeypatch.setattr(Path, "mkdir", fail_mkdir)

    out = run_recon._output_dir(tmp_path / "requested", "U3")

    assert out.is_dir()
    assert out.name.startswith("sas_legacy_recon_U3_")
    probe = out / "write-test"
    probe.write_text("ok", encoding="utf-8")
    probe.unlink()


def test_warehouse_uses_sdk_config_when_environment_is_missing(monkeypatch):
    for name in (
        "DATABRICKS_DEMO_HOST",
        "DATABRICKS_DEMO_TOKEN",
        "DATABRICKS_HOST",
        "DATABRICKS_TOKEN",
    ):
        monkeypatch.delenv(name, raising=False)

    class Config:
        host = "https://x"

        @staticmethod
        def authenticate():
            return {"Authorization": "Bearer t"}

    class WorkspaceClient:
        config = Config()

    sdk = types.ModuleType("databricks.sdk")
    sdk.WorkspaceClient = WorkspaceClient
    databricks = types.ModuleType("databricks")
    databricks.sdk = sdk
    monkeypatch.setitem(sys.modules, "databricks", databricks)
    monkeypatch.setitem(sys.modules, "databricks.sdk", sdk)

    warehouse = Warehouse("wh")

    assert warehouse.base == "https://x"
    assert warehouse._s.headers["Authorization"] == "Bearer t"


def test_warehouse_raises_without_environment_or_sdk(monkeypatch):
    for name in (
        "DATABRICKS_DEMO_HOST",
        "DATABRICKS_DEMO_TOKEN",
        "DATABRICKS_HOST",
        "DATABRICKS_TOKEN",
    ):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setitem(sys.modules, "databricks.sdk", None)

    with pytest.raises(WarehouseError):
        Warehouse("wh")
