#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import subprocess
import time
import urllib.error
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PYTHON = ROOT / "backend" / ".venv" / "bin" / "python"


def request_json(
    base_url: str,
    path: str,
    *,
    method: str = "GET",
    token: str | None = None,
    payload: dict | None = None,
) -> dict:
    body = None if payload is None else json.dumps(payload, ensure_ascii=False).encode("utf-8")
    headers = {"Accept": "application/json"}
    if body is not None:
        headers["Content-Type"] = "application/json"
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(f"{base_url}{path}", data=body, method=method, headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=25) as response:
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


def assert_publication_safety(record: dict) -> None:
    if record["external_write_performed"] is not False:
        raise AssertionError("knowledge publication must not perform external channel writes")
    if record["model_call_performed"] is not False:
        raise AssertionError("knowledge publication smoke must not perform model calls")


def main() -> None:
    if not PYTHON.exists():
        raise SystemExit(f"backend python not found: {PYTHON}")

    port = int(os.getenv("P3_06U_26H2W2_PUBLISH_FLOW_PORT", "8127"))
    base_url = f"http://127.0.0.1:{port}"
    output_dir = Path(os.getenv("P3_06U_26H2W2_PUBLISH_FLOW_OUTPUT", ROOT / "output" / "p3_06u_26h2w2_publish_flow"))
    output_dir.mkdir(parents=True, exist_ok=True)
    db_path = output_dir / "publish_flow.sqlite"
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
                    "tenant_slug": f"h2w2-publish-{stamp}",
                    "tenant_name": "H2W2 知识发布流程验收空间",
                    "owner_name": "H2W2 管理员",
                    "email": f"h2w2-publish-{stamp}@wanfa.local",
                    "password": f"H2W2Publish{stamp}!",
                },
            )
            token = owner["access_token"]
            tenant_id = owner["user"]["tenant"]["id"]
            headers = {"token": token}

            document = request_json(
                base_url,
                f"/api/tenants/{tenant_id}/knowledge-documents",
                method="POST",
                token=token,
                payload={
                    "title": "H2W2 售后流程政策",
                    "source_type": "manual_document",
                    "source_uri": "internal://h2w2/after-sales-policy",
                    "raw_text": (
                        "标准产品保修期为三年。七天内未拆封可申请退换。"
                        "超过七天需要核对订单时间、商品状态和质量问题。"
                        "所有退款不承诺立即到账，涉及投诉、举报或赔偿诉求必须转人工处理。"
                    ),
                    "tags": ["售后", "流程政策", "转人工规则"],
                    "status": "draft",
                    "chunk_size": 80,
                    "chunk_overlap": 10,
                },
            )
            if document["status"] != "draft" or document["ingestion_status"] != "indexed":
                raise AssertionError(f"unexpected document state: {document['status']} / {document['ingestion_status']}")

            evaluation_set = request_json(
                base_url,
                f"/api/tenants/{tenant_id}/knowledge-evaluation-sets",
                method="POST",
                token=token,
                payload={
                    "name": "H2W2 发布前样题",
                    "description": "用于验证流程政策发布前能命中文档、引用来源和必含词。",
                    "status": "active",
                    "evaluation_mode": "customer_service_retrieval",
                    "cases": [
                        {
                            "question": "标准产品保修期多久",
                            "expected_terms": ["三年", "保修"],
                            "expected_source_uri": "internal://h2w2/after-sales-policy",
                            "required_citation": True,
                        },
                        {
                            "question": "超过七天退换需要核对什么",
                            "expected_terms": ["订单时间", "商品状态", "质量问题"],
                            "expected_source_uri": "internal://h2w2/after-sales-policy",
                            "required_citation": True,
                        },
                    ],
                },
            )
            payload = {
                "evaluation_set_id": evaluation_set["id"],
                "search_status": "draft",
                "top_k": 8,
                "low_confidence_threshold": 0.1,
                "min_hit_rate": 1.0,
                "min_citation_coverage": 1.0,
                "min_expected_term_coverage": 1.0,
                "ignore_safe_handoff_failures": True,
            }
            precheck = request_json(
                base_url,
                f"/api/knowledge-documents/{document['id']}/publish-checks",
                method="POST",
                token=token,
                payload=payload,
            )
            if precheck["can_publish"] is not True or precheck["published"] is not False:
                raise AssertionError(f"publish precheck did not pass: {precheck['blocking_reasons']}")
            if len(precheck["case_results"]) != 2:
                raise AssertionError("publish precheck did not evaluate the two sample cases")

            history_after_precheck = request_json(
                base_url,
                f"/api/knowledge-documents/{document['id']}/publications",
                token=token,
            )
            precheck_record = history_after_precheck["items"][0]
            if precheck_record["publication_type"] != "publish_check" or precheck_record["status"] != "passed":
                raise AssertionError(f"unexpected precheck record: {precheck_record}")
            assert_publication_safety(precheck_record)

            published = request_json(
                base_url,
                f"/api/knowledge-documents/{document['id']}/publication",
                method="POST",
                token=token,
                payload=payload,
            )
            if published["published"] is not True or published["document"]["status"] != "active":
                raise AssertionError(f"document was not published: {published['blocking_reasons']}")

            history_after_publish = request_json(
                base_url,
                f"/api/knowledge-documents/{document['id']}/publications",
                token=token,
            )
            publish_record = history_after_publish["items"][0]
            if publish_record["publication_type"] != "publish" or publish_record["status"] != "published":
                raise AssertionError(f"unexpected publish record: {publish_record}")
            assert_publication_safety(publish_record)

            print(
                json.dumps(
                    {
                        "tenant_id": tenant_id,
                        "document_id": document["id"],
                        "evaluation_set_id": evaluation_set["id"],
                        "precheck_status": precheck_record["status"],
                        "publish_status": publish_record["status"],
                        "history_total": history_after_publish["total"],
                        "checked_case_count": len(precheck["case_results"]),
                        "external_write_performed": publish_record["external_write_performed"],
                        "model_call_performed": publish_record["model_call_performed"],
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
