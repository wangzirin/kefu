#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PYTHON = ROOT / "backend" / ".venv" / "bin" / "python"


def request_json(base_url: str, path: str, *, method: str = "GET", token: str | None = None, payload: dict | None = None) -> dict:
    body = None if payload is None else json.dumps(payload, ensure_ascii=False).encode("utf-8")
    headers = {"Accept": "application/json"}
    if body is not None:
        headers["Content-Type"] = "application/json"
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(f"{base_url}{path}", data=body, method=method, headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"{method} {path} failed: HTTP {exc.code} {detail[:500]}") from exc


def wait_for_health(base_url: str, process: subprocess.Popen[str]) -> None:
    started = time.time()
    while time.time() - started < 25:
        if process.poll() is not None:
            raise RuntimeError(f"backend exited early with code {process.returncode}")
        try:
            request_json(base_url, "/health")
            return
        except Exception:
            time.sleep(0.3)
    raise RuntimeError("backend health check timed out")


def main() -> None:
    if not PYTHON.exists():
        raise SystemExit(f"backend python not found: {PYTHON}")

    port = int(os.getenv("P3_06U_26H2W2_REPLY_STRATEGY_PORT", "8126"))
    base_url = f"http://127.0.0.1:{port}"
    output_dir = Path(os.getenv("P3_06U_26H2W2_REPLY_STRATEGY_OUTPUT", ROOT / "output" / "p3_06u_26h2w2_reply_strategy"))
    output_dir.mkdir(parents=True, exist_ok=True)
    db_path = output_dir / "reply_strategy.sqlite"
    db_path.unlink(missing_ok=True)
    subprocess.run([str(PYTHON), "scripts/repair_local_sqlite_schema.py", "--db", str(db_path)], cwd=ROOT, check=True)

    env = {
        **os.environ,
        "DATABASE_URL": f"sqlite+pysqlite:///{db_path}",
        "STANDARD_OPS_ENV": "development",
        "OUTBOX_EXTERNAL_WRITE_ENABLED": "false",
    }
    log_path = output_dir / "backend.log"
    with log_path.open("w", encoding="utf-8") as log_file:
        process = subprocess.Popen(
            [str(PYTHON), "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", str(port)],
            cwd=ROOT / "backend",
            env=env,
            stdout=log_file,
            stderr=log_file,
            text=True,
        )
        try:
            wait_for_health(base_url, process)
            stamp = str(int(time.time()))
            owner = request_json(
                base_url,
                "/api/auth/local-setup/owner",
                method="POST",
                payload={
                    "tenant_slug": f"h2w2-reply-{stamp}",
                    "tenant_name": "H2W2 自动回复策略验收空间",
                    "owner_name": "H2W2 管理员",
                    "email": f"h2w2-reply-{stamp}@wanfa.local",
                    "password": f"H2W2Reply{stamp}!",
                },
            )
            token = owner["access_token"]
            tenant_id = owner["user"]["tenant"]["id"]
            initial = request_json(base_url, f"/api/tenants/{tenant_id}/reply-strategy", token=token)
            if initial["source"] != "default_empty_policy":
                raise AssertionError(f"unexpected initial policy source: {initial['source']}")

            saved = request_json(
                base_url,
                f"/api/tenants/{tenant_id}/reply-strategy",
                method="PATCH",
                token=token,
                payload={
                    "blocked_policy_terms": ["私下转账", "绕过平台", "保证收益", "无条件退款"],
                    "manual_review_terms": ["投诉", "起诉", "赔偿", "差评", "封号"],
                    "force_draft_only": True,
                },
            )
            reread = request_json(base_url, f"/api/tenants/{tenant_id}/reply-strategy", token=token)
            policy = reread["reply_policy"]
            if "无条件退款" not in policy["blocked_policy_terms"]:
                raise AssertionError("blocked policy term was not persisted")
            if "封号" not in policy["manual_review_terms"]:
                raise AssertionError("manual review term was not persisted")
            if policy["force_draft_only"] is not True:
                raise AssertionError("force draft-only flag was not persisted")
            if saved["external_write_performed"] or reread["model_call_performed"]:
                raise AssertionError("reply strategy API must not perform external writes or model calls")

            print(
                json.dumps(
                    {
                        "tenant_id": tenant_id,
                        "initial_source": initial["source"],
                        "strategy_version": reread["strategy_version"],
                        "blocked_policy_terms": len(policy["blocked_policy_terms"]),
                        "manual_review_terms": len(policy["manual_review_terms"]),
                        "force_draft_only": policy["force_draft_only"],
                        "external_write_performed": reread["external_write_performed"],
                        "model_call_performed": reread["model_call_performed"],
                        "status": "ok",
                    },
                    ensure_ascii=False,
                    indent=2,
                )
            )
        finally:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)


if __name__ == "__main__":
    main()
