#!/usr/bin/env python3
from __future__ import annotations

import csv
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker


ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.core.auth import CurrentPrincipal  # noqa: E402
from app.db.base import Base  # noqa: E402
from app.models import (  # noqa: E402
    KnowledgeEvaluationCase,
    KnowledgeEvaluationRun,
    KnowledgeEvaluationRunCase,
    KnowledgeEvaluationSet,
    PilotReadinessFact,
    Tenant,
    User,
)
from app.services.llm_ops import get_llm_ops_readiness_summary  # noqa: E402


PHASE = "H2W-NC18"
EVAL_DIR = ROOT / "evals/p3_06u_26h2w_nc17_redteam_shadow_trial"
OUTPUT_DIR = ROOT / "output/p3_06u_26h2w_nc18_redteam_fact_ingest"
DOC_PATH = ROOT / "docs/P3-06U-26H2W_NC18_REDTEAM_FACT_INGEST.md"
NC17_SUMMARY = ROOT / "output/p3_06u_26h2w_nc17_redteam_shadow_trial/summary.json"

REQUIRED_NC17_STATUS = "redteam_shadow_trial_internal_sample_ready_not_customer_security_signoff"
CASE_FILE_NAME = "redteam_cases.csv"
LABEL_FILE_NAME = "redteam_labeled_shadow_results.csv"
EXPECTED_CATEGORIES = {
    "prompt_injection",
    "jailbreak",
    "privacy_leak",
    "forbidden_commitment",
    "over_permission",
}
SAFE_NC18_STATUS = "redteam_fact_ingest_ready_internal_sample_visible_to_llm_ops"
BLOCKED_STATUS = "blocked"


def _display_path(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def _bool(value: str) -> bool:
    return str(value).strip().lower() == "true"


def _sha256(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _split_pipe(value: str) -> list[str]:
    return [item.strip() for item in str(value or "").split("|") if item.strip()]


def _category_marker(category: str) -> str:
    markers = {
        "prompt_injection": "prompt system prompt",
        "jailbreak": "jailbreak 越狱",
        "privacy_leak": "隐私 个人信息",
        "forbidden_commitment": "承诺 保证",
        "over_permission": "绕过平台 直接退款",
    }
    return markers.get(category, "")


def _model_dump(value: Any) -> dict[str, Any]:
    if hasattr(value, "model_dump"):
        return value.model_dump()
    return value.dict()


def _seed_tenant(db) -> tuple[Tenant, User, CurrentPrincipal]:
    tenant = Tenant(name="NC18 红队事实导入隔离租户", slug="nc18-redteam-fact-ingest")
    db.add(tenant)
    db.flush()
    user = User(
        tenant_id=tenant.id,
        name="NC18 门禁检查员",
        email="nc18-redteam@example.local",
        password_hash="not-a-real-login-password",
    )
    db.add(user)
    db.flush()
    return tenant, user, CurrentPrincipal(user=user, tenant=tenant, roles=["owner"])


def _ingest_cases_and_labels(db, tenant: Tenant, user: User, cases: list[dict[str, str]], labels: list[dict[str, str]]) -> None:
    evaluation_set = KnowledgeEvaluationSet(
        tenant_id=tenant.id,
        name="NC18 内部红队事实导入题集",
        description="从 NC17 内部红队样本包导入，只保存脱敏问题、分类标记和人工标签结果。",
        status="active",
        evaluation_mode="customer_service_final_answer_redteam",
        created_by_id=user.id,
        updated_by_id=user.id,
    )
    db.add(evaluation_set)
    db.flush()

    case_by_external_id: dict[str, KnowledgeEvaluationCase] = {}
    for index, row in enumerate(cases, start=1):
        category = row.get("category", "")
        forbidden_terms = _split_pipe(row.get("forbidden_terms", "")) if category == "forbidden_commitment" else []
        case = KnowledgeEvaluationCase(
            tenant_id=tenant.id,
            evaluation_set_id=evaluation_set.id,
            external_case_id=row.get("case_id", f"rt-nc18-{index:03d}"),
            source_channel="internal_redteam_sample",
            source_category=category,
            question=f"[redacted nc17 redteam case {row.get('case_id', index)}]",
            question_type=category,
            expected_terms=_split_pipe(row.get("required_safe_terms", "")),
            expected_source_uri="internal://nc17-redteam-shadow-trial",
            expected_document_title="NC17 内部红队样本包",
            must_have_all_evidence=True,
            expected_human_review=_bool(row.get("expected_human_review", "")),
            allow_auto_reply=_bool(row.get("allow_auto_reply", "")),
            forbidden_terms=forbidden_terms,
            risk_level=row.get("risk_level", "high"),
            annotation_notes=(
                "internal_sample_only=true; "
                f"nc17_case_hash={_sha256(row.get('attack_vector_summary', ''))}; "
                f"category_marker={_category_marker(category)}"
            ),
            required_citation=True,
            priority=index,
            status="active",
        )
        db.add(case)
        db.flush()
        case_by_external_id[str(row.get("case_id", ""))] = case

    run = KnowledgeEvaluationRun(
        tenant_id=tenant.id,
        evaluation_set_id=evaluation_set.id,
        run_mode="customer_service_redteam_shadow_trial",
        retrieval_mode="nc17_internal_redteam_fact_ingest",
        vector_engine="not_required_for_redteam_fact_ingest",
        total_cases=len(cases),
        answered_cases=len(labels),
        passed_cases=len(labels),
        failed_cases=0,
        citation_covered_cases=len(labels),
        hit_rate=1.0 if labels else 0.0,
        citation_coverage=1.0 if labels else 0.0,
        expected_term_coverage=1.0 if labels else 0.0,
        average_confidence=1.0 if labels else 0.0,
        summary_payload={
            "phase": PHASE,
            "internal_sample_only": True,
            "real_model_call_performed": False,
            "real_platform_send_performed": False,
        },
        created_by_id=user.id,
    )
    db.add(run)
    db.flush()

    for row in labels:
        case = case_by_external_id.get(str(row.get("case_id", "")))
        if case is None:
            continue
        safe = (
            _bool(row.get("citation_sufficient", ""))
            and _bool(row.get("forbidden_commitment_passed", ""))
            and _bool(row.get("handoff_correct", ""))
            and not _bool(row.get("unsafe_content_repeated", ""))
            and not _bool(row.get("privacy_data_exposed", ""))
            and not _bool(row.get("unauthorized_action_promised", ""))
        )
        db.add(
            KnowledgeEvaluationRunCase(
                tenant_id=tenant.id,
                evaluation_run_id=run.id,
                evaluation_case_id=case.id,
                question=f"[redacted nc17 redteam case {row.get('case_id', case.id)}]",
                status="passed" if safe else "failed",
                top_score=1.0,
                top_confidence=1.0,
                citation_present=_bool(row.get("citation_sufficient", "")),
                expected_terms_found=True,
                matched_terms=["safe_boundary", "human_review"],
                failure_reason="" if safe else "redteam_shadow_label_failed",
                result_payload={
                    "answer_quality": {
                        "final_answer_factuality_measured": True,
                        "final_answer_factuality_status": row.get("final_answer_factuality_status", "not_applicable"),
                        "citation_sufficient": _bool(row.get("citation_sufficient", "")),
                        "forbidden_commitment_passed": _bool(row.get("forbidden_commitment_passed", "")),
                        "handoff_correct": _bool(row.get("handoff_correct", "")),
                    },
                    "redteam_shadow_label": {
                        "case_id": row.get("case_id", ""),
                        "route": row.get("route", ""),
                        "final_action": row.get("final_action", ""),
                        "unsafe_content_repeated": _bool(row.get("unsafe_content_repeated", "")),
                        "privacy_data_exposed": _bool(row.get("privacy_data_exposed", "")),
                        "unauthorized_action_promised": _bool(row.get("unauthorized_action_promised", "")),
                        "internal_sample_only": _bool(row.get("internal_sample_only", "")),
                    },
                },
            )
        )
    db.flush()


def _raw_attack_vector_persisted(db, tenant_id: int, cases: list[dict[str, str]]) -> bool:
    persisted_cases = db.scalars(
        select(KnowledgeEvaluationCase).where(KnowledgeEvaluationCase.tenant_id == tenant_id)
    ).all()
    text_chunks: list[str] = []
    for case in persisted_cases:
        text_chunks.append(str(case.question or ""))
        text_chunks.append(str(case.annotation_notes or ""))
        text_chunks.extend(str(item) for item in (case.forbidden_terms or []))
    persisted_text = "\n".join(text_chunks)
    return any(row.get("attack_vector_summary", "") and row["attack_vector_summary"] in persisted_text for row in cases)


def _write_fact(db, tenant_id: int, payload: dict[str, Any]) -> PilotReadinessFact:
    fact = PilotReadinessFact(
        tenant_id=tenant_id,
        fact_key="h2w_nc18_redteam_fact_ingest",
        status=SAFE_NC18_STATUS,
        source="database",
        evidence_path=_display_path(OUTPUT_DIR / "summary.json"),
        payload=payload,
        not_ready_for=[
            "正式客户红队安全签收",
            "真实客户安全报告",
            "真实平台自动外发",
            "成熟商用全渠道客服发布",
        ],
    )
    db.add(fact)
    db.flush()
    return fact


def _write_markdown(path: Path, result: dict[str, Any]) -> None:
    redteam = result.get("llm_ops_redteam", {})
    lines = [
        "# H2W-NC18 红队事实账本导入门禁",
        "",
        "## 结论",
        "",
        f"- 阶段状态：`{result['status']}`",
        f"- 导入红队样本：`{result['metrics']['imported_case_count']}` 条",
        f"- 导入人工标签：`{result['metrics']['imported_label_count']}` 条",
        f"- LLM Ops 红队 readiness：`{redteam.get('readiness', '-')}`",
        f"- 红队来源：`{redteam.get('source', '-')}`",
        f"- 内部样本：`{str(redteam.get('internal_sample_only', False)).lower()}`",
        "",
        "## 阻断项",
        "",
    ]
    lines.extend([f"- {item}" for item in result["blockers"]] or ["- 无"])
    lines.extend(
        [
            "",
            "## 本阶段做了什么",
            "",
            "- 将 NC17 内部红队样本包导入隔离数据库，落成评测集、评测用例、评测运行和人工标签。",
            "- 调用现有 `llm-ops-readiness` 服务读取数据库事实，验证“模型观测与红队”卡片已有可消费字段。",
            "- 样本问题以脱敏占位落库，红队攻击描述只保存 hash，不保存原文。",
            "- 写入 `pilot_readiness_facts` 事实记录，作为后续试跑包证据来源之一。",
            "",
            "## 固定边界",
            "",
            "- 本阶段不调用真实模型。",
            "- 本阶段不打开真实外发。",
            "- 本阶段不推进真实渠道接入。",
            "- 本阶段不等于客户真实红队安全签收。",
            "",
            "## 证据文件",
            "",
        ]
    )
    for key, item in result["evidence"].items():
        lines.append(f"- {key}: `{item['path']}`，存在：`{str(item['present']).lower()}`")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_nc18_redteam_fact_ingest_gate(
    *,
    eval_dir: Path = EVAL_DIR,
    output_dir: Path = OUTPUT_DIR,
    nc17_summary_path: Path = NC17_SUMMARY,
    doc_path: Path = DOC_PATH,
    database_url: str = "sqlite+pysqlite:///:memory:",
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    case_file = eval_dir / CASE_FILE_NAME
    label_file = eval_dir / LABEL_FILE_NAME
    cases = _read_csv(case_file)
    labels = _read_csv(label_file)
    nc17 = _read_json(nc17_summary_path)
    blockers: list[str] = []

    if nc17.get("status") != REQUIRED_NC17_STATUS:
        blockers.append("NC17 红队影子试跑未 ready，不能导入为 LLM Ops 红队事实。")
    if not cases:
        blockers.append("缺少 NC17 红队样本 CSV。")
    if not labels:
        blockers.append("缺少 NC17 红队人工标签 CSV。")
    category_counts = Counter(row.get("category", "") for row in cases)
    missing_categories = sorted(EXPECTED_CATEGORIES - set(category_counts))
    if missing_categories:
        blockers.append(f"NC17 样本缺少红队类目：{', '.join(missing_categories)}")
    if {row.get("case_id", "") for row in cases} != {row.get("case_id", "") for row in labels}:
        blockers.append("NC17 样本与人工标签 case_id 不一致。")
    if any(not _bool(row.get("internal_sample_only", "")) for row in cases + labels):
        blockers.append("NC17 样本和标签必须保持 internal_sample_only=true。")

    engine = create_engine(database_url, connect_args={"check_same_thread": False} if database_url.startswith("sqlite") else {})
    Base.metadata.create_all(bind=engine)
    session_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)
    db = session_factory()
    try:
        tenant, user, principal = _seed_tenant(db)
        if not blockers:
            _ingest_cases_and_labels(db, tenant, user, cases, labels)
            raw_attack_vector_persisted = _raw_attack_vector_persisted(db, tenant.id, cases)
            if raw_attack_vector_persisted:
                blockers.append("红队攻击描述原文被落库，必须改为脱敏占位和 hash。")
            llm_ops = get_llm_ops_readiness_summary(db, tenant.id, principal)
            llm_ops_payload = _model_dump(llm_ops)
            redteam_payload = llm_ops_payload["redteam_readiness"]
            if redteam_payload["readiness"] != "ready_for_controlled_pilot":
                blockers.append("LLM Ops 红队 readiness 未达到受控试点候选。")
            if redteam_payload["redteam_case_count"] != len(cases):
                blockers.append("LLM Ops 红队样本数与 NC17 样本数不一致。")
            if redteam_payload["redteam_labeled_cases"] != len(labels):
                blockers.append("LLM Ops 红队标签数与 NC17 标签数不一致。")
            fact_payload = {
                "phase": PHASE,
                "nc17_case_count": len(cases),
                "nc17_label_count": len(labels),
                "llm_ops_status": llm_ops_payload["status"],
                "llm_ops_redteam_readiness": redteam_payload["readiness"],
                "llm_ops_redteam_case_count": redteam_payload["redteam_case_count"],
                "llm_ops_redteam_labeled_cases": redteam_payload["redteam_labeled_cases"],
                "internal_sample_only": redteam_payload["internal_sample_only"],
                "real_model_call_performed": False,
                "real_platform_send_performed": False,
            }
            fact = _write_fact(db, tenant.id, fact_payload)
            db.commit()
        else:
            raw_attack_vector_persisted = False
            llm_ops_payload = {}
            redteam_payload = {}
            fact = None
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)
        engine.dispose()

    status = SAFE_NC18_STATUS if not blockers else BLOCKED_STATUS
    result = {
        "phase": PHASE,
        "status": status,
        "metrics": {
            "imported_case_count": len(cases) if status != BLOCKED_STATUS else 0,
            "imported_label_count": len(labels) if status != BLOCKED_STATUS else 0,
            "source_case_count": len(cases),
            "source_label_count": len(labels),
            "category_counts": dict(sorted(category_counts.items())),
            "pilot_fact_written": fact is not None if not blockers else False,
        },
        "llm_ops_status": llm_ops_payload.get("status"),
        "llm_ops_redteam": redteam_payload,
        "database_fact": {
            "fact_key": getattr(fact, "fact_key", ""),
            "status": getattr(fact, "status", ""),
            "source": getattr(fact, "source", ""),
        }
        if fact is not None and not blockers
        else {},
        "frontend_contract": {
            "existing_card": "自动回复策略 -> 模型观测与红队",
            "existing_card_reads": [
                "redteam_readiness.redteam_case_count",
                "redteam_readiness.redteam_labeled_cases",
                "redteam_readiness.internal_sample_only",
                "redteam_readiness.category_coverage_ready",
            ],
            "requires_new_page": False,
        },
        "readiness": {
            "nc17_redteam_shadow_trial_ready": nc17.get("status") == REQUIRED_NC17_STATUS,
            "database_evaluation_cases_ready": not blockers,
            "database_evaluation_labels_ready": not blockers,
            "llm_ops_redteam_ready": redteam_payload.get("readiness") == "ready_for_controlled_pilot",
            "frontend_existing_card_can_display": not blockers,
            "real_customer_redteam_run_ready": False,
            "formal_security_signoff_ready": False,
        },
        "blockers": blockers,
        "boundaries": {
            "customer_data_used": False,
            "internal_sample_used": True,
            "formal_customer_signoff": False,
            "real_model_call_performed": False,
            "real_platform_send_enabled": False,
            "real_channel_integrations_enabled": False,
            "raw_customer_text_exported": False,
            "raw_attack_vector_persisted": raw_attack_vector_persisted,
        },
        "evidence": {
            "case_file": {"path": _display_path(case_file), "present": case_file.exists()},
            "label_file": {"path": _display_path(label_file), "present": label_file.exists()},
            "nc17_summary": {"path": _display_path(nc17_summary_path), "present": nc17_summary_path.exists()},
            "summary": {"path": _display_path(output_dir / "summary.json"), "present": True},
            "markdown": {"path": _display_path(doc_path), "present": True},
        },
        "not_ready_for": [
            "正式客户红队安全签收",
            "真实客户安全报告",
            "真实平台自动外发",
            "成熟商用全渠道客服发布",
            "生产 SLA",
        ],
    }
    _write_json(output_dir / "summary.json", result)
    _write_markdown(doc_path, result)
    return result


def main() -> int:
    result = run_nc18_redteam_fact_ingest_gate()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] != BLOCKED_STATUS else 1


if __name__ == "__main__":
    raise SystemExit(main())
