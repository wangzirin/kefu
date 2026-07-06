#!/usr/bin/env python3

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator


ROOT = Path(__file__).resolve().parents[1]
BACKEND_ROOT = ROOT / "backend"
SCRIPTS_ROOT = ROOT / "scripts"
DEFAULT_KNOWLEDGE_PACKAGE = ROOT / "evals/p3_06u_26f_real_customer_knowledge_package_template.json"
DEFAULT_EVAL_BANK = ROOT / "evals/p3_01_realistic_customer_service_eval_bank_62_2026-06-27.csv"
DEFAULT_OUTPUT_DIR = ROOT / "output/p3_06u_26h2w11a_owner_rehearsal"

for path in (BACKEND_ROOT, SCRIPTS_ROOT):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from app.services.model_gateway import (  # noqa: E402
    DETERMINISTIC_PROVIDER,
    ModelDraftKnowledge,
    ModelDraftRequest,
    generate_reply_draft,
)
from import_customer_service_eval_bank import run_customer_service_eval_bank_import  # noqa: E402
from run_p2_24_synthetic_eval_smoke import (  # noqa: E402
    _json_response,
    _local_test_client,
    _safe_local_embedding_env,
)


KNOWLEDGE_UPDATE_PACKAGE_SCHEMA_VERSION = "wanfa.knowledge_update_package.v1"
SAFE_NEGATION_PREFIXES = ("不能", "不得", "不会", "不应", "避免", "禁止", "不直接", "不要")
POLICY_RISK_TERMS = (
    "保证转化",
    "保证转化率",
    "保证 ROI",
    "保证最低价",
    "保证不封号",
    "永不出错",
    "无条件退款",
    "马上赔偿",
    "我们全责",
    "删除审计",
    "冒充人工",
)


@contextmanager
def _safe_h2w11_env() -> Iterator[None]:
    keys = [
        "STANDARD_OPS_ENV",
        "STANDARD_OPS_DEV_BOOTSTRAP_ENABLED",
        "OUTBOX_EXTERNAL_WRITE_ENABLED",
        "TRUSTED_INBOUND_WORKER_ENABLED",
        "BAILIAN_API_KEY",
        "DEEPSEEK_API_KEY",
    ]
    old_values = {key: os.environ.get(key) for key in keys}
    os.environ["STANDARD_OPS_ENV"] = "production"
    os.environ["STANDARD_OPS_DEV_BOOTSTRAP_ENABLED"] = "false"
    os.environ["OUTBOX_EXTERNAL_WRITE_ENABLED"] = "false"
    os.environ["TRUSTED_INBOUND_WORKER_ENABLED"] = "false"
    os.environ["BAILIAN_API_KEY"] = ""
    os.environ["DEEPSEEK_API_KEY"] = ""
    try:
        yield
    finally:
        for key, value in old_values.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value


def _auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _write_text(path: Path, body: str) -> dict[str, Any]:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")
    return {
        "path": str(path),
        "sha256": _sha256_text(body),
        "bytes": len(body.encode("utf-8")),
    }


def _load_template_package(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    documents = data.get("documents") if isinstance(data.get("documents"), list) else []
    if len(documents) < 7:
        raise ValueError("H2W-11A knowledge package must include at least 7 documents")
    return data


def _knowledge_update_package_from_template(path: Path) -> dict[str, Any]:
    template = _load_template_package(path)
    documents = []
    for item in template["documents"]:
        documents.append(
            {
                "title": str(item["title"]).strip(),
                "source_type": "knowledge_update_package",
                "source_uri": str(item["source_uri"]).strip(),
                "raw_text": str(item["raw_text"]).strip(),
                "tags": [str(tag).strip() for tag in item.get("tags") or [] if str(tag).strip()],
                "status": "active",
                "chunk_size": int(item.get("chunk_size") or 1600),
                "chunk_overlap": int(item.get("chunk_overlap") or 120),
            }
        )
    return {
        "schema_version": KNOWLEDGE_UPDATE_PACKAGE_SCHEMA_VERSION,
        "package_id": "h2w11a-customer-knowledge-template-20260704",
        "package_name": "H2W-11A 客户知识包演练模板",
        "source_diagnostic_filename": "",
        "notes": "负责人试点演练使用的脱敏知识包模板；不含客户聊天原文，不触发外部写入或模型调用。",
        "knowledge_documents": documents,
    }


def _bootstrap_owner_with_real_login(client) -> dict[str, Any]:
    setup_before = _json_response(
        client.get("/api/auth/local-setup/status"),
        expected_status=200,
        label="local setup status before owner setup",
    )
    if not setup_before["can_create_first_owner"]:
        raise RuntimeError(f"local setup should allow first owner in empty rehearsal DB: {setup_before}")

    owner_payload = {
        "tenant_slug": "h2w11a-owner-rehearsal",
        "tenant_name": "H2W-11A 负责人演练空间",
        "owner_name": "负责人",
        "email": "h2w11a-owner@wanfa.local",
        "password": "H2W11AOwner123!",
    }
    owner_created = _json_response(
        client.post("/api/auth/local-setup/owner", json=owner_payload),
        expected_status=201,
        label="create first local owner",
    )
    login = _json_response(
        client.post(
            "/api/auth/login",
            json={
                "tenant_slug": owner_payload["tenant_slug"],
                "email": owner_payload["email"],
                "password": owner_payload["password"],
            },
        ),
        expected_status=200,
        label="owner login with password",
    )
    me = _json_response(
        client.get("/api/auth/me", headers=_auth_headers(login["access_token"])),
        expected_status=200,
        label="owner /me after real login",
    )
    setup_after = _json_response(
        client.get("/api/auth/local-setup/status"),
        expected_status=200,
        label="local setup status after owner setup",
    )
    tenant_id = int(login["user"]["tenant"]["id"])
    return {
        "tenant_id": tenant_id,
        "tenant_slug": login["user"]["tenant"]["slug"],
        "owner_user_id": int(login["user"]["id"]),
        "owner_email_hash": _sha256_text(owner_payload["email"])[:24],
        "token": login["access_token"],
        "setup_before": {
            "initialized": setup_before["initialized"],
            "can_create_first_owner": setup_before["can_create_first_owner"],
            "local_deployment_ready": setup_before["local_deployment_ready"],
            "blockers": setup_before["blockers"],
        },
        "setup_after": {
            "initialized": setup_after["initialized"],
            "can_create_first_owner": setup_after["can_create_first_owner"],
            "first_owner_creation_locked": setup_after["first_owner_creation_locked"],
            "local_deployment_ready": setup_after["local_deployment_ready"],
            "blockers": setup_after["blockers"],
        },
        "checks": {
            "created_by_local_setup_owner_endpoint": owner_created["user"]["roles"] == ["owner"],
            "login_used_password_endpoint": login["token_type"] == "bearer",
            "me_matches_login_user": me["id"] == login["user"]["id"],
            "dev_bootstrap_disabled": setup_after["dev_bootstrap_enabled"] is False,
            "external_write_disabled": setup_after["external_write_enabled"] is False,
            "trusted_inbound_worker_disabled": setup_after["trusted_inbound_worker_enabled"] is False,
        },
    }


def _import_knowledge_package(client, *, tenant_id: int, token: str, path: Path) -> dict[str, Any]:
    headers = _auth_headers(token)
    package = _knowledge_update_package_from_template(path)
    preview = _json_response(
        client.post(
            f"/api/tenants/{tenant_id}/knowledge-update-package/previews",
            headers=headers,
            json={"package": package},
        ),
        expected_status=200,
        label="preview H2W-11A knowledge update package",
    )
    imported = _json_response(
        client.post(
            f"/api/tenants/{tenant_id}/knowledge-update-package-imports",
            headers=headers,
            json={"package": package},
        ),
        expected_status=201,
        label="import H2W-11A knowledge update package",
    )
    documents = _json_response(
        client.get(f"/api/tenants/{tenant_id}/knowledge-documents?status=active&page_size=100", headers=headers),
        expected_status=200,
        label="list imported knowledge documents",
    )
    chunk_count = 0
    for document in documents["items"]:
        chunks = _json_response(
            client.get(f"/api/knowledge-documents/{document['id']}/chunks", headers=headers),
            expected_status=200,
            label=f"list chunks for document {document['id']}",
        )
        chunk_count += len(chunks)
    return {
        "template_path": str(path),
        "package_id": imported["package_id"],
        "package_name": imported["package_name"],
        "preview_operation_counts": preview["operation_counts"],
        "import_operation_counts": imported["operation_counts"],
        "import_batch_id": imported["import_batch_id"],
        "document_count": documents["total"],
        "chunk_count": chunk_count,
        "safety": imported["safety"],
        "checks": {
            "preview_can_apply": preview["can_apply"] is True,
            "import_can_apply": imported["can_apply"] is True,
            "import_batch_created": imported["import_batch_id"] is not None,
            "minimum_7_documents_active": documents["total"] >= 7,
            "chunks_created": chunk_count >= documents["total"],
            "provider_call_performed_false": imported["safety"].get("provider_call_performed") is False,
            "external_write_performed_false": imported["safety"].get("external_write_performed") is False,
        },
    }


def _import_question_bank(client, *, tenant_id: int, token: str, path: Path) -> dict[str, Any]:
    import_result = run_customer_service_eval_bank_import(
        input_path=path,
        name="H2W-11A 负责人试点脱敏题库 62 题",
        description="负责人真实登录 rehearsal：客户式脱敏题库，不含真实客户身份或真实订单资料。",
        status="active",
        create=False,
    )
    if import_result["status"] != "validated":
        raise RuntimeError(f"question bank validation failed: {import_result['status']}")
    payload = dict(import_result["payload"])
    payload["source_label"] = "h2w11a_desensitized_owner_rehearsal_bank"
    payload["minimum_case_count"] = 50
    payload["maximum_case_count"] = 100
    headers = _auth_headers(token)
    precheck = _json_response(
        client.post(
            f"/api/tenants/{tenant_id}/customer-service-question-banks/precheck",
            headers=headers,
            json=payload,
        ),
        expected_status=200,
        label="precheck H2W-11A question bank",
    )
    imported = _json_response(
        client.post(
            f"/api/tenants/{tenant_id}/customer-service-question-banks/import",
            headers=headers,
            json=payload,
        ),
        expected_status=201,
        label="import H2W-11A question bank",
    )
    return {
        "path": str(path),
        "evaluation_set_id": imported["evaluation_set_id"],
        "case_count": imported["case_count"],
        "coverage_summary": imported["coverage_summary"],
        "precheck_status": precheck["status"],
        "import_status": imported["status"],
        "case_catalog_sample": import_result["case_catalog"][:8],
        "checks": {
            "precheck_can_import": precheck["can_import"] is True,
            "imported": imported["imported"] is True,
            "evaluation_set_created": imported["evaluation_set_id"] is not None,
            "case_count_50_to_100": 50 <= imported["case_count"] <= 100,
            "no_sensitive_rows": imported["coverage_summary"].get("sensitive_row_count") == 0,
            "raw_text_not_returned": imported["raw_text_included"] is False,
            "provider_call_performed_false": imported["provider_call_performed"] is False,
            "external_write_performed_false": imported["external_write_performed"] is False,
        },
    }


def _contains_safe_negation(text: str, term: str) -> bool:
    index = text.find(term)
    if index < 0:
        return False
    window = text[max(0, index - 8) : index]
    return any(prefix in window for prefix in SAFE_NEGATION_PREFIXES)


def _forbidden_hits(text: str, terms: list[str]) -> list[str]:
    hits: list[str] = []
    for raw in terms:
        term = str(raw or "").strip()
        if term and term in text and not _contains_safe_negation(text, term):
            hits.append(term)
    return sorted(set(hits))


def _top_match(case_result: dict[str, Any]) -> dict[str, Any]:
    payload = case_result.get("result_payload") or {}
    top_match = payload.get("top_match")
    return top_match if isinstance(top_match, dict) else {}


def _knowledge_from_case(case_result: dict[str, Any]) -> list[ModelDraftKnowledge]:
    top = _top_match(case_result)
    if not top:
        return []
    return [
        ModelDraftKnowledge(
            title=str(top.get("document_title") or ""),
            answer=str(top.get("content_preview") or ""),
            source_uri=str(top.get("source_uri") or ""),
            matched_terms=[str(term) for term in case_result.get("matched_terms") or []],
        )
    ]


def _label_for_case(case_result: dict[str, Any], draft_text: str, *, human_review_required: bool) -> dict[str, Any]:
    payload = case_result.get("result_payload") or {}
    forbidden_terms = [str(term) for term in payload.get("forbidden_terms") or []]
    forbidden_hits = _forbidden_hits(draft_text, forbidden_terms + list(POLICY_RISK_TERMS))
    expected_human_review = bool(payload.get("expected_human_review"))
    allow_auto_reply = bool(payload.get("allow_auto_reply", True))
    risk_level = str(payload.get("risk_level") or "low")
    citation_sufficient = bool(case_result.get("citation_present")) and bool(_top_match(case_result))
    expected_terms_found = bool(case_result.get("expected_terms_found"))
    expected_handoff = expected_human_review or not allow_auto_reply or risk_level in {"high", "critical"}
    payload_predicted_handoff = payload.get("predicted_human_review")
    predicted_handoff = (
        bool(payload_predicted_handoff)
        if isinstance(payload_predicted_handoff, bool)
        else human_review_required or not citation_sufficient
    )
    handoff_correct = bool(expected_handoff) == bool(predicted_handoff)
    forbidden_commitment_passed = not forbidden_hits

    if expected_handoff and predicted_handoff and handoff_correct and forbidden_commitment_passed:
        status = "not_applicable"
    elif expected_handoff or predicted_handoff:
        status = "needs_human_review"
    elif citation_sufficient and expected_terms_found and forbidden_commitment_passed:
        status = "correct"
    elif citation_sufficient and forbidden_commitment_passed:
        status = "partially_correct"
    else:
        status = "incorrect"

    return {
        "evaluation_run_case_id": int(case_result["id"]),
        "final_answer_factuality_status": status,
        "citation_sufficient": citation_sufficient,
        "forbidden_commitment_passed": forbidden_commitment_passed,
        "handoff_correct": handoff_correct,
        "reviewer_notes": "",
    }


def _run_evaluation_and_answer_quality(
    client,
    *,
    tenant_id: int,
    token: str,
    evaluation_set_id: int,
    top_k: int,
) -> dict[str, Any]:
    headers = _auth_headers(token)
    run = _json_response(
        client.post(
            f"/api/knowledge-evaluation-sets/{evaluation_set_id}/runs",
            headers=headers,
            json={"top_k": top_k, "low_confidence_threshold": 0.2},
        ),
        expected_status=201,
        label="run H2W-11A evaluation set",
    )
    labels: list[dict[str, Any]] = []
    draft_catalog: list[dict[str, Any]] = []
    for case_result in run["case_results"]:
        payload = case_result.get("result_payload") or {}
        draft = generate_reply_draft(
            ModelDraftRequest(
                user_message=str(case_result.get("question") or ""),
                intent=str(payload.get("question_type") or "standard_customer_question"),
                knowledge=_knowledge_from_case(case_result),
                provider=DETERMINISTIC_PROVIDER,
                confidence=float(case_result.get("top_confidence") or 0.0),
                risk_level=str(payload.get("risk_level") or "low"),
            )
        )
        top = _top_match(case_result)
        citation_uris = [str(top.get("source_uri"))] if top.get("source_uri") else []
        sample = _json_response(
            client.patch(
                f"/api/knowledge-evaluation-run-cases/{case_result['id']}/final-answer-sample",
                headers=headers,
                json={
                    "final_answer_text": draft.draft_text,
                    "final_answer_source": "dry_run_fixture",
                    "citation_uris": citation_uris,
                    "answer_author": "H2W-11A 本地确定性回复器",
                    "reviewer_notes": "",
                },
            ),
            expected_status=200,
            label=f"capture final answer sample for case {case_result['id']}",
        )
        label = _label_for_case(case_result, draft.draft_text, human_review_required=draft.human_review_required)
        labels.append(label)
        draft_catalog.append(
            {
                "external_case_id": payload.get("external_case_id") or "",
                "question_hash": _sha256_text(str(case_result.get("question") or ""))[:24],
                "draft_hash": _sha256_text(draft.draft_text)[:24],
                "draft_chars": len(draft.draft_text),
                "source_uri": citation_uris[0] if citation_uris else "",
                "label": label["final_answer_factuality_status"],
                "sample_coverage_after_case": sample["final_answer_sample_coverage"],
            }
        )

    labeled = _json_response(
        client.patch(
            f"/api/knowledge-evaluation-runs/{run['id']}/factuality-labels/batch",
            headers=headers,
            json={"labels": labels},
        ),
        expected_status=200,
        label="batch label H2W-11A final answer factuality",
    )
    updated_run = labeled["updated_run"]
    markdown_report = _json_response(
        client.get(f"/api/knowledge-evaluation-runs/{run['id']}/report?format=markdown", headers=headers),
        expected_status=200,
        label="export H2W-11A markdown evaluation report",
    )
    csv_report = _json_response(
        client.get(f"/api/knowledge-evaluation-runs/{run['id']}/report?format=csv", headers=headers),
        expected_status=200,
        label="export H2W-11A csv evaluation report",
    )
    final_answer_export = _json_response(
        client.get(
            f"/api/knowledge-evaluation-runs/{run['id']}/final-answer-labels/export"
            "?format=csv&include_answer_text=false",
            headers=headers,
        ),
        expected_status=200,
        label="export H2W-11A final answer labels",
    )
    return {
        "run_id": run["id"],
        "evaluation_set_id": evaluation_set_id,
        "initial_run": _compact_run(run),
        "updated_run": _compact_run(updated_run),
        "labeled_cases": labeled["labeled_cases"],
        "final_answer_factuality_rate": labeled["final_answer_factuality_rate"],
        "final_answer_factuality_labeled_cases": labeled["final_answer_factuality_labeled_cases"],
        "draft_catalog_sample": draft_catalog[:12],
        "reports": {
            "markdown": markdown_report,
            "csv": csv_report,
            "final_answer_labels_csv": final_answer_export,
        },
        "checks": {
            "evaluation_run_completed": run["total_cases"] == 62,
            "final_answer_samples_captured": updated_run["summary_payload"].get("final_answer_sampled_cases") == 62,
            "factuality_labels_recorded": labeled["final_answer_factuality_labeled_cases"] == 62,
            "report_raw_text_excluded": markdown_report["raw_text_included"] is False
            and csv_report["raw_text_included"] is False,
            "final_answer_text_excluded_from_label_export": final_answer_export["final_answer_text_included"] is False,
            "provider_call_performed_false": markdown_report["provider_call_performed"] is False
            and csv_report["provider_call_performed"] is False
            and final_answer_export["provider_call_performed"] is False,
            "external_write_performed_false": markdown_report["external_write_performed"] is False
            and csv_report["external_write_performed"] is False
            and final_answer_export["external_write_performed"] is False,
        },
    }


def _compact_run(run: dict[str, Any]) -> dict[str, Any]:
    summary = run.get("summary_payload") or {}
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
        "failed_cases": run["failed_cases"],
        "needs_review_cases": run["needs_review_cases"],
        "citation_covered_cases": run["citation_covered_cases"],
        "hit_rate": run["hit_rate"],
        "citation_coverage": run["citation_coverage"],
        "expected_term_coverage": run["expected_term_coverage"],
        "average_confidence": run["average_confidence"],
        "unsupported_answer_rate": run["unsupported_answer_rate"],
        "final_answer_sampled_cases": summary.get("final_answer_sampled_cases"),
        "final_answer_sample_coverage": summary.get("final_answer_sample_coverage"),
        "final_answer_factuality_labeled_cases": summary.get("final_answer_factuality_labeled_cases"),
        "final_answer_factuality_rate": summary.get("final_answer_factuality_rate"),
        "human_review_correctness": summary.get("human_review_correctness"),
        "knowledge_gap_rate": summary.get("knowledge_gap_rate"),
        "customer_service_metrics_version": summary.get("customer_service_metrics_version"),
    }


def _customer_quality_report_and_signoff(client, *, tenant_id: int, token: str) -> dict[str, Any]:
    headers = _auth_headers(token)
    report = _json_response(
        client.get(f"/api/tenants/{tenant_id}/customer-quality-report", headers=headers),
        expected_status=200,
        label="get H2W-11A customer quality report",
    )
    exported = _json_response(
        client.get(f"/api/tenants/{tenant_id}/customer-quality-report/export?format=html", headers=headers),
        expected_status=200,
        label="export H2W-11A customer quality report",
    )
    signoff = _json_response(
        client.post(
            f"/api/tenants/{tenant_id}/customer-quality-report/signoffs",
            headers=headers,
            json={
                "signoff_status": "accepted_with_notes",
                "signer_name": "负责人",
                "signer_role": "本地负责人",
                "signer_organization": "H2W-11A 试点空间",
                "confirmation_method": "local_record",
                "notes": "负责人确认本轮为受控演练证据，正式客户验收前需要替换真实脱敏题库和人工标签。",
            },
        ),
        expected_status=201,
        label="record H2W-11A local report signoff",
    )
    signoffs = _json_response(
        client.get(f"/api/tenants/{tenant_id}/customer-quality-report/signoffs", headers=headers),
        expected_status=200,
        label="list H2W-11A customer quality report signoffs",
    )
    return {
        "report": {
            "schema_version": report["schema_version"],
            "period": report["period"],
            "report_status": report["report_status"],
            "report_status_label": report["report_status_label"],
            "report_confidence_score": report["report_confidence_score"],
            "latest_evaluation_run_id": report["latest_evaluation_run_id"],
            "raw_text_included": report["raw_text_included"],
            "model_call_performed": report["model_call_performed"],
            "external_platform_write_performed": report["external_platform_write_performed"],
        },
        "export": exported,
        "signoff": {
            "signoff_status": signoff["signoff_status"],
            "signoff_status_label": signoff["signoff_status_label"],
            "signer_display_name": signoff["signer_display_name"],
            "confirmation_method": signoff["confirmation_method"],
            "notes_recorded": signoff["notes_recorded"],
            "raw_text_included": signoff["raw_text_included"],
            "final_answer_text_included": signoff["final_answer_text_included"],
            "reviewer_notes_included": signoff["reviewer_notes_included"],
            "signer_name_raw_included": signoff["signer_name_raw_included"],
            "electronic_signature_performed": signoff["electronic_signature_performed"],
            "formal_contract_signoff_performed": signoff["formal_contract_signoff_performed"],
            "model_call_performed": signoff["model_call_performed"],
            "external_platform_write_performed": signoff["external_platform_write_performed"],
        },
        "signoff_list_total": signoffs["total"],
        "checks": {
            "customer_quality_report_generated": report["latest_evaluation_run_id"] is not None,
            "customer_quality_report_exported": exported["body_bytes"] > 0,
            "local_signoff_recorded": signoff["signoff_status"] == "accepted_with_notes",
            "signoff_list_contains_record": signoffs["total"] >= 1,
            "no_raw_text_or_final_answer_text_in_signoff": signoff["raw_text_included"] is False
            and signoff["final_answer_text_included"] is False
            and signoff["signer_name_raw_included"] is False,
            "formal_signature_not_performed": signoff["electronic_signature_performed"] is False
            and signoff["formal_contract_signoff_performed"] is False,
            "provider_call_performed_false": report["model_call_performed"] is False
            and exported["model_call_performed"] is False
            and signoff["model_call_performed"] is False,
            "external_platform_write_performed_false": report["external_platform_write_performed"] is False
            and exported["external_platform_write_performed"] is False
            and signoff["external_platform_write_performed"] is False,
        },
    }


def _write_outputs(output_dir: Path, result: dict[str, Any], evaluation: dict[str, Any], quality: dict[str, Any]) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    report_files = {
        "evaluation_markdown": _write_text(
            output_dir / evaluation["reports"]["markdown"]["filename"],
            evaluation["reports"]["markdown"]["body"],
        ),
        "evaluation_csv": _write_text(
            output_dir / evaluation["reports"]["csv"]["filename"],
            evaluation["reports"]["csv"]["body"],
        ),
        "final_answer_labels_csv": _write_text(
            output_dir / evaluation["reports"]["final_answer_labels_csv"]["filename"],
            evaluation["reports"]["final_answer_labels_csv"]["body"],
        ),
        "customer_quality_report_html": _write_text(
            output_dir / quality["export"]["filename"],
            quality["export"]["body"],
        ),
    }
    safe_result = json.loads(json.dumps(result, ensure_ascii=False))
    safe_result["output_files"] = report_files
    (output_dir / "summary.json").write_text(json.dumps(safe_result, ensure_ascii=False, indent=2), encoding="utf-8")
    result["output_dir"] = str(output_dir)
    result["output_files"] = report_files


def run_h2w11a_owner_rehearsal(
    *,
    knowledge_package_path: Path | str = DEFAULT_KNOWLEDGE_PACKAGE,
    eval_bank_path: Path | str = DEFAULT_EVAL_BANK,
    top_k: int = 8,
    output_dir: Path | str | None = None,
) -> dict[str, Any]:
    package_path = Path(knowledge_package_path)
    bank_path = Path(eval_bank_path)
    with _safe_h2w11_env(), _safe_local_embedding_env(), _local_test_client() as client:
        owner = _bootstrap_owner_with_real_login(client)
        tenant_id = owner["tenant_id"]
        token = owner["token"]
        knowledge = _import_knowledge_package(client, tenant_id=tenant_id, token=token, path=package_path)
        bank = _import_question_bank(client, tenant_id=tenant_id, token=token, path=bank_path)
        evaluation = _run_evaluation_and_answer_quality(
            client,
            tenant_id=tenant_id,
            token=token,
            evaluation_set_id=int(bank["evaluation_set_id"]),
            top_k=top_k,
        )
        quality = _customer_quality_report_and_signoff(client, tenant_id=tenant_id, token=token)

    owner_public = {key: value for key, value in owner.items() if key != "token"}
    checks = {
        **{f"owner.{key}": value for key, value in owner_public["checks"].items()},
        **{f"knowledge.{key}": value for key, value in knowledge["checks"].items()},
        **{f"question_bank.{key}": value for key, value in bank["checks"].items()},
        **{f"evaluation.{key}": value for key, value in evaluation["checks"].items()},
        **{f"quality.{key}": value for key, value in quality["checks"].items()},
    }
    blockers = [name for name, passed in checks.items() if not passed]
    result = {
        "schema_version": "p3-06u-26h2w11a.owner_rehearsal.v1",
        "status": "completed" if not blockers else "blocked",
        "phase": "H2W-11A",
        "ready_for_h2w11b": not blockers,
        "checks": checks,
        "blockers": blockers,
        "owner_login": owner_public,
        "knowledge_package": knowledge,
        "question_bank": bank,
        "evaluation": {
            key: value
            for key, value in evaluation.items()
            if key not in {"reports"}
        },
        "customer_quality_report": {
            "report": quality["report"],
            "signoff": quality["signoff"],
            "signoff_list_total": quality["signoff_list_total"],
        },
        "boundaries": {
            "real_customer_data_used": False,
            "real_platform_send_performed": False,
            "external_platform_write_performed": False,
            "provider_call_performed": False,
            "formal_contract_signoff_performed": False,
            "local_signoff_record_performed": True,
            "dev_bootstrap_login_used": False,
            "real_password_login_used": True,
        },
        "limitations": [
            "本轮仍使用客户式脱敏样例题库，不是正式客户原始题库。",
            "最终答案样本由本地确定性回复器生成，用于门禁 rehearsal，不代表云端大模型真实质量。",
            "签收是本地记录，不是电子签章或合同签收。",
            "真实渠道外发、真实平台回执和官方 IM sandbox 仍未启用。",
        ],
        "next_actions": [
            "用真实客户脱敏 50-100 题替换样例题库后复跑本脚本。",
            "把客户负责人/客服主管人工标签导入最终答案事实性评测。",
            "进入 H2W-11B：前端逐页试点使用 rehearsal，把报告、知识发布、维护入口与客户可理解文案对齐。",
        ],
    }
    if output_dir is not None:
        _write_outputs(Path(output_dir), result, evaluation, quality)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Run H2W-11A owner-login customer-service rehearsal locally.")
    parser.add_argument("--knowledge-package", type=Path, default=DEFAULT_KNOWLEDGE_PACKAGE)
    parser.add_argument("--eval-bank", type=Path, default=DEFAULT_EVAL_BANK)
    parser.add_argument("--top-k", type=int, default=8)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args()
    result = run_h2w11a_owner_rehearsal(
        knowledge_package_path=args.knowledge_package,
        eval_bank_path=args.eval_bank,
        top_k=args.top_k,
        output_dir=args.output_dir,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] == "completed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
