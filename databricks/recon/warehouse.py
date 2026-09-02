"""Minimal Statement Execution API client (one warehouse window per recon run).

Auth: DATABRICKS_DEMO_HOST / DATABRICKS_DEMO_TOKEN (fallback DATABRICKS_HOST / DATABRICKS_TOKEN).
Values are never logged.
"""

from __future__ import annotations

import os
import time

import requests

Rows = list[dict[str, str | None]]


class WarehouseError(RuntimeError):
    pass


class Warehouse:
    def __init__(self, warehouse_id: str, host: str | None = None, token: str | None = None):
        self.warehouse_id = warehouse_id
        host = host or os.environ.get("DATABRICKS_DEMO_HOST") or os.environ.get("DATABRICKS_HOST")
        token = (
            token or os.environ.get("DATABRICKS_DEMO_TOKEN") or os.environ.get("DATABRICKS_TOKEN")
        )
        if not host or not token:
            raise WarehouseError(
                "Databricks credentials missing: set DATABRICKS_DEMO_HOST and DATABRICKS_DEMO_TOKEN"
            )
        self.base = host.rstrip("/")
        if not self.base.startswith("http"):
            self.base = "https://" + self.base
        self._s = requests.Session()
        self._s.headers["Authorization"] = f"Bearer {token}"
        self.statements = 0
        self.elapsed_s = 0.0

    def _get(self, path: str) -> dict:
        r = self._s.get(self.base + path, timeout=120)
        r.raise_for_status()
        return r.json()

    def query(self, sql: str, poll_s: float = 2.0, timeout_s: float = 900) -> Rows:
        t0 = time.time()
        self.statements += 1
        r = self._s.post(
            self.base + "/api/2.0/sql/statements",
            json={
                "warehouse_id": self.warehouse_id,
                "statement": sql,
                "wait_timeout": "50s",
                "disposition": "INLINE",
                "format": "JSON_ARRAY",
            },
            timeout=120,
        )
        r.raise_for_status()
        body = r.json()
        sid = body["statement_id"]
        while body["status"]["state"] in ("PENDING", "RUNNING"):
            if time.time() - t0 > timeout_s:
                raise WarehouseError(f"statement {sid} timed out after {timeout_s}s")
            time.sleep(poll_s)
            body = self._get(f"/api/2.0/sql/statements/{sid}")
        state = body["status"]["state"]
        if state != "SUCCEEDED":
            err = body["status"].get("error", {})
            raise WarehouseError(f"statement {state}: {err.get('message', '')}\n{sql[:500]}")
        cols = [c["name"] for c in body.get("manifest", {}).get("schema", {}).get("columns", [])]
        data = list(body.get("result", {}).get("data_array") or [])
        nxt = body.get("result", {}).get("next_chunk_internal_link")
        while nxt:
            chunk = self._get(nxt)
            data.extend(chunk.get("data_array") or [])
            nxt = chunk.get("next_chunk_internal_link")
        self.elapsed_s += time.time() - t0
        return [dict(zip(cols, row)) for row in data]

    def fetch(self, sql: str) -> Rows:
        return self.query(sql)

    def upload_file(self, local_path: str, remote_path: str) -> None:
        with open(local_path, "rb") as body:
            r = self._s.put(
                self.base + "/api/2.0/fs/files/" + remote_path.lstrip("/") + "?overwrite=true",
                data=body,
                timeout=120,
            )
        r.raise_for_status()

    def execute(self, sql: str) -> None:
        self.query(sql)
