#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import os
import sys
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool


ROOT = Path(__file__).resolve().parents[1]
BACKEND_ROOT = ROOT / "backend"
SCRIPTS_ROOT = ROOT / "scripts"
DEFAULT_SEED_DOCUMENTS = ROOT / "evals" / "p2_24_seed_knowledge_documents.json"
DEFAULT_EVAL_BANK = ROOT / "evals" / "customer_service_eval_bank_synthetic_80_2026-06-26.csv"

for path in (BACKEND_ROOT, SCRIPTS_ROOT):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from fastapi.testclient import TestClient  # noqa: E402

from app.db.base import Base  # noqa: E402
from app.db.session import get_db  # noqa: E402
from app.main import create_app  # noqa: E402
from import_customer_service_eval_bank import run_customer_service_eval_bank_import  # noqa: E402


@contextmanager
def _safe_local_embedding_env() -> Iterator[None]:
    keys = [
        "KNOWLEDGE_EMBEDDING_PROVIDER",
        "KNOWLEDGE_EMBEDDING_API_BASE",
        "KNOWLEDGE_EMBEDDING_API_KEY",
        "KNOWLEDGE_VECTOR_STORE",
        "KNOWLEDGE_RERANKER",
        "OUTBOX_EXTERNAL_WRITE_ENABLED",
    ]
    old_values = {key: os.environ.get(key) for key in keys}
    os.environ["KNOWLEDGE_EMBEDDING_PROVIDER"] = "deterministic_local"
    os.environ["KNOWLEDGE_EMBEDDING_API_BASE"] = ""
    os.environ["KNOWLEDGE_EMBEDDING_API_KEY"] = ""
    os.environ["KNOWLEDGE_VECTOR_STORE"] = "sqlite_json_vector_store"
    os.environ["KNOWLEDGE_RERANKER"] = "lexical_overlap_reranker_v1"
    os.environ["OUTBOX_EXTERNAL_WRITE_ENABLED"] = "false"
    try:
        yield
    finally:
        for key, value in old_values.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value


@contextmanager
def _local_test_client() -> Iterator[TestClient]:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    factory = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)
    app = create_app()

    def override_db() -> Iterator[Session]:
        session = factory()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_db
    try:
        with TestClient(app) as client:
            yield client
    finally:
        app.dependency_overrides.clear()
        Base.metadata.drop_all(bind=engine)


def _json_response(response, *, expected_status: int, label: str) -> dict:
    if response.status_code != expected_status:
        raise RuntimeError(f"{label} failed: status={response.status_code}, body={response.text[:500]}")
    return response.json()


def _bootstrap_owner(client: TestClient) -> tuple[dict, dict, str]:
    tenant = _json_response(
        client.post("/api/tenants", json={"name": "P2-24 合成评测空间", "slug": "p2-24-synthetic-eval"}),
        expected_status=201,
        label="create tenant",
    )
    role = _json_response(
        client.post(f"/api/tenants/{tenant['id']}/roles", json={"code": "owner", "name": "Owner"}),
        expected_status=201,
        label="create owner role",
    )
    user = _json_response(
        client.post(
            f"/api/tenants/{tenant['id']}/users",
            json={"name": "P2-24 Owner", "email": "p2-24-owner@example.com", "password": "ChangeMe123!"},
        ),
        expected_status=201,
        label="create owner user",
    )
    _json_response(
        client.post(f"/api/users/{user['id']}/roles", json={"role_id": role["id"]}),
        expected_status=201,
        label="assign owner role",
    )
    login = _json_response(
        client.post(
            "/api/auth/login",
            json={
                "tenant_slug": tenant["slug"],
                "email": "p2-24-owner@example.com",
                "password": "ChangeMe123!",
            },
        ),
        expected_status=200,
        label="owner login",
    )
    return tenant, user, login["access_token"]


def _load_seed_documents(path: Path) -> list[dict]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list) or not data:
        raise ValueError("seed document file must contain a non-empty list")
    return [dict(item) for item in data]


def _import_seed_documents(client: TestClient, *, tenant_id: int, token: str, path: Path) -> dict:
    headers = {"Authorization": f"Bearer {token}"}
    documents: list[dict] = []
    chunk_count = 0
    for item in _load_seed_documents(path):
        payload = {
            "title": str(item["title"]).strip(),
            "source_type": str(item.get("source_type") or "synthetic_seed_document"),
            "source_uri": str(item["source_uri"]).strip(),
            "raw_text": str(item["raw_text"]).strip(),
            "tags": item.get("tags") or [],
            "status": "active",
            "chunk_size": int(item.get("chunk_size") or 4000),
            "chunk_overlap": int(item.get("chunk_overlap") or 0),
        }
        document = _json_response(
            client.post(f"/api/tenants/{tenant_id}/knowledge-documents", headers=headers, json=payload),
            expected_status=201,
            label=f"import seed document {payload['source_uri']}",
        )
        documents.append(
            {
                "id": document["id"],
                "title": document["title"],
                "source_uri": document["source_uri"],
                "chunk_count": document["chunk_count"],
            }
        )
        chunk_count += int(document["chunk_count"])
    return {"documents": documents, "chunk_count": chunk_count}


def _create_evaluation_set_from_bank(
    client: TestClient,
    *,
    tenant_id: int,
    token: str,
    eval_bank_path: Path,
) -> tuple[dict, dict]:
    import_result = run_customer_service_eval_bank_import(
        input_path=eval_bank_path,
        name="P2-24 合成脱敏客服验收题库 80题",
        description="P2-24 本地 smoke：seed 知识文档 + P2-23 合成脱敏题库；不含真实客户资料。",
        status="active",
        create=False,
    )
    if import_result["status"] != "validated":
        raise RuntimeError(f"evaluation bank validation failed: {import_result}")
    payload = import_result["payload"]
    headers = {"Authorization": f"Bearer {token}"}
    evaluation_set = _json_response(
        client.post(f"/api/tenants/{tenant_id}/knowledge-evaluation-sets", headers=headers, json=payload),
        expected_status=201,
        label="create evaluation set",
    )
    return import_result, evaluation_set


def _compact_run(run: dict) -> dict:
    summary = run["summary_payload"]
    return {
        "id": run["id"],
        "evaluation_set_id": run["evaluation_set_id"],
        "run_mode": run["run_mode"],
        "retrieval_mode": run["retrieval_mode"],
        "vector_engine": run["vector_engine"],
        "total_cases": run["total_cases"],
        "answered_cases": run["answered_cases"],
        "no_hit_cases": run["no_hit_cases"],
        "passed_cases": run["passed_cases"],
        "needs_review_cases": run["needs_review_cases"],
        "hit_rate": run["hit_rate"],
        "citation_coverage": run["citation_coverage"],
        "expected_term_coverage": run["expected_term_coverage"],
        "average_confidence": run["average_confidence"],
        "unsupported_answer_rate": run["unsupported_answer_rate"],
        "human_review_correctness": summary.get("human_review_correctness"),
        "knowledge_gap_rate": summary.get("knowledge_gap_rate"),
        "forbidden_term_hits": summary.get("forbidden_term_hits"),
        "summary_payload": {
            "evaluation_scope": summary.get("evaluation_scope"),
            "unsupported_answer_rate_measured": summary.get("unsupported_answer_rate_measured"),
            "embedding_provider": summary.get("embedding_provider"),
            "vector_store": summary.get("vector_store"),
            "retrieval_backend": summary.get("retrieval_backend"),
            "reranker": summary.get("reranker"),
            "top_k": summary.get("top_k"),
            "low_confidence_threshold": summary.get("low_confidence_threshold"),
            "customer_service_metrics_version": summary.get("customer_service_metrics_version"),
        },
    }


def _compact_report(report: dict) -> dict:
    return {
        "format": report["report_format"],
        "filename": report["filename"],
        "raw_text_included": report["raw_text_included"],
        "provider_call_performed": report["provider_call_performed"],
        "external_write_performed": report["external_write_performed"],
        "body_preview": report["body"][:1600],
    }


def run_p2_24_synthetic_eval_smoke(
    *,
    seed_documents_path: Path | str = DEFAULT_SEED_DOCUMENTS,
    eval_bank_path: Path | str = DEFAULT_EVAL_BANK,
    top_k: int = 5,
    low_confidence_threshold: float = 0.2,
    output_dir: Path | str | None = None,
) -> dict:
    seed_path = Path(seed_documents_path)
    bank_path = Path(eval_bank_path)
    with _safe_local_embedding_env(), _local_test_client() as client:
        tenant, _, token = _bootstrap_owner(client)
        imported = _import_seed_documents(client, tenant_id=tenant["id"], token=token, path=seed_path)
        import_result, evaluation_set = _create_evaluation_set_from_bank(
            client,
            tenant_id=tenant["id"],
            token=token,
            eval_bank_path=bank_path,
        )
        headers = {"Authorization": f"Bearer {token}"}
        run = _json_response(
            client.post(
                f"/api/knowledge-evaluation-sets/{evaluation_set['id']}/runs",
                headers=headers,
                json={"top_k": top_k, "low_confidence_threshold": low_confidence_threshold},
            ),
            expected_status=201,
            label="run evaluation set",
        )
        markdown_report = _json_response(
            client.get(f"/api/knowledge-evaluation-runs/{run['id']}/report?format=markdown", headers=headers),
            expected_status=200,
            label="export markdown report",
        )
        csv_report = _json_response(
            client.get(f"/api/knowledge-evaluation-runs/{run['id']}/report?format=csv", headers=headers),
            expected_status=200,
            label="export csv report",
        )

    result = {
        "status": "completed",
        "phase": "P2-24",
        "seed_documents_file": str(seed_path),
        "eval_bank_file": str(bank_path),
        "raw_text_logged": False,
        "provider_call_performed": False,
        "external_platform_write_performed": False,
        "internal_database_write_performed": True,
        "seed_document_count": len(imported["documents"]),
        "seed_chunk_count": imported["chunk_count"],
        "seed_documents": imported["documents"],
        "evaluation_set": {
            "id": evaluation_set["id"],
            "case_count": evaluation_set["case_count"],
            "evaluation_mode": evaluation_set["evaluation_mode"],
        },
        "run": _compact_run(run),
        "reports": {
            "markdown": _compact_report(markdown_report),
            "csv": _compact_report(csv_report),
        },
        "case_catalog_sample": import_result["case_catalog"][:5],
    }
    if output_dir is not None:
        out = Path(output_dir)
        out.mkdir(parents=True, exist_ok=True)
        (out / "p2_24_synthetic_eval_smoke_summary.json").write_text(
            json.dumps(result, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        (out / markdown_report["filename"]).write_text(markdown_report["body"], encoding="utf-8")
        (out / csv_report["filename"]).write_text(csv_report["body"], encoding="utf-8")
        result["output_dir"] = str(out)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Run P2-24 synthetic customer-service evaluation smoke locally.")
    parser.add_argument("--seed-documents", type=Path, default=DEFAULT_SEED_DOCUMENTS)
    parser.add_argument("--eval-bank", type=Path, default=DEFAULT_EVAL_BANK)
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--low-confidence-threshold", type=float, default=0.2)
    parser.add_argument("--output-dir", type=Path, default=None)
    args = parser.parse_args()

    result = run_p2_24_synthetic_eval_smoke(
        seed_documents_path=args.seed_documents,
        eval_bank_path=args.eval_bank,
        top_k=args.top_k,
        low_confidence_threshold=args.low_confidence_threshold,
        output_dir=args.output_dir,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
