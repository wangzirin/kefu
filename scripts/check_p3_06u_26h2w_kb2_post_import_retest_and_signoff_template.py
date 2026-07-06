#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PHASE = "H2W-KB2"
DEFAULT_OUTPUT_DIR = ROOT / "output/p3_06u_26h2w_kb2_post_import_retest_and_signoff_template"
DOC_PATH = ROOT / "docs/P3-06U-26H2W_KB2_POST_IMPORT_RETEST_AND_SIGNOFF_TEMPLATE.md"

KB1_SUMMARY = ROOT / "output/p3_06u_26h2w_kb1_customer_specific_knowledge_package_rehearsal/summary.json"
KB1_PACKAGE = ROOT / "evals/p3_06u_26h2w_kb1_customer_specific_knowledge_package_rehearsal.json"
OPS1_SUMMARY = ROOT / "output/p3_06u_26h2w_ops1_after_sales_handoff_rehearsal/summary.json"

SIGNOFF_COLUMNS = [
    "signoff_item_id",
    "section",
    "item_name",
    "evidence_summary",
    "expected_reviewer",
    "review_status",
    "customer_comment",
    "confirmed_by",
    "confirmed_at",
    "needs_change",
    "not_formal_signoff",
]

REQUIRED_KNOWLEDGE_TYPES = {
    "business_object",
    "standard_qa",
    "process_policy",
    "forbidden_commitment",
    "handoff_rule",
}

OVERCLAIM_PHRASES = [
    "正式客户签收已完成",
    "客户专属知识库正式验收完成",
    "客户专属知识库正式就绪",
    "正式准确率签收已完成",
    "真实平台自动外发已接通",
    "真实外发已开启",
    "企业渠道真实上线已完成",
]


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=SIGNOFF_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)


def _display_path(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def _flag(payload: dict[str, Any], *path: str) -> Any:
    current: Any = payload
    for key in path:
        if not isinstance(current, dict):
            return None
        current = current.get(key)
    return current


def _int_value(value: Any, default: int = -1) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _package_metrics(package: dict[str, Any]) -> dict[str, Any]:
    cards = package.get("object_knowledge_cards") or []
    docs = package.get("knowledge_documents") or []
    sets = package.get("evaluation_sets") or []
    cases = [case for item in sets for case in item.get("cases", [])]
    knowledge_types = sorted(
        {
            str((card.get("scope") or {}).get("knowledge_type") or "").strip()
            for card in cards
            if str((card.get("scope") or {}).get("knowledge_type") or "").strip()
        }
    )
    return {
        "business_object_count": len(package.get("business_objects") or []),
        "object_knowledge_card_count": len(cards),
        "knowledge_document_count": len(docs),
        "evaluation_set_count": len(sets),
        "regression_case_count": len(cases),
        "knowledge_types": knowledge_types,
        "auto_reply_case_count": len([case for case in cases if case.get("allow_auto_reply") is True]),
        "handoff_case_count": len([case for case in cases if case.get("expected_human_review") is True]),
        "source_uri_count": len({doc.get("source_uri") for doc in docs if doc.get("source_uri")}),
        "cases": cases,
    }


def _load_upstream_summary(path: Path, *, name: str, expected_status: str) -> tuple[dict[str, Any], list[str]]:
    if not path.exists():
        return {}, [f"{name} 上游 summary 缺失：{_display_path(path)}"]
    try:
        payload = _read_json(path)
    except json.JSONDecodeError:
        return {}, [f"{name} 上游 summary 不是有效 JSON：{_display_path(path)}"]
    status = str(payload.get("status") or "")
    if status != expected_status:
        return payload, [f"{name} 上游状态不满足：期望 {expected_status}，实际 {status or 'missing'}"]
    return payload, []


def _upstream_boundary_blockers(payload: dict[str, Any], *, name: str) -> list[str]:
    blockers: list[str] = []
    checks = {
        "正式客户签收": (
            _flag(payload, "readiness", "formal_customer_signoff_ready") is True
            or _flag(payload, "boundaries", "formal_customer_signoff_performed") is True
            or _flag(payload, "signoff_boundary", "customer_confirmed") is True
            or _flag(payload, "signoff_boundary", "formal_contract_signoff_performed") is True
        ),
        "真实平台外发": (
            _flag(payload, "readiness", "real_platform_send_ready") is True
            or _flag(payload, "boundaries", "real_platform_send_performed") is True
            or _flag(payload, "boundaries", "external_platform_write_performed") is True
        ),
        "真实客户数据": _flag(payload, "boundaries", "real_customer_data_used") is True,
        "客户专属知识库正式就绪": (
            _flag(payload, "readiness", "customer_specific_knowledge_ready") is True
            or _flag(payload, "boundaries", "customer_specific_knowledge_ready") is True
        ),
        "模型 provider 调用": _flag(payload, "boundaries", "provider_call_performed") is True,
    }
    for label, failed in checks.items():
        if failed:
            blockers.append(f"{name} 上游越界记录为已完成或已启用：{label}")
    return blockers


def _validate_package_and_kb1_summary(
    *,
    package: dict[str, Any],
    kb1_summary: dict[str, Any],
) -> tuple[list[str], dict[str, Any], dict[str, bool]]:
    blockers: list[str] = []
    package_metrics = _package_metrics(package)
    summary_metrics = kb1_summary.get("package_metrics") if isinstance(kb1_summary.get("package_metrics"), dict) else {}
    backend = kb1_summary.get("backend_rehearsal") if isinstance(kb1_summary.get("backend_rehearsal"), dict) else {}
    preview = backend.get("preview") if isinstance(backend.get("preview"), dict) else {}
    imported = backend.get("import") if isinstance(backend.get("import"), dict) else {}
    rollback = backend.get("rollback") if isinstance(backend.get("rollback"), dict) else {}
    safety = imported.get("safety") if isinstance(imported.get("safety"), dict) else {}

    package_checks = {
        "package_schema_ok": package.get("schema_version") == "wanfa.knowledge_update_package.v1",
        "package_is_internal_rehearsal": "内部脱敏" in str(package.get("notes") or "")
        and "不是正式客户签收" in str(package.get("notes") or ""),
        "business_objects_enough": package_metrics["business_object_count"] >= 3,
        "knowledge_cards_enough": package_metrics["object_knowledge_card_count"] >= 8,
        "documents_enough": package_metrics["knowledge_document_count"] >= 5,
        "regression_cases_enough": package_metrics["regression_case_count"] >= 8,
        "knowledge_types_complete": REQUIRED_KNOWLEDGE_TYPES.issubset(set(package_metrics["knowledge_types"])),
        "auto_reply_cases_enough": package_metrics["auto_reply_case_count"] >= 5,
        "handoff_cases_enough": package_metrics["handoff_case_count"] >= 3,
        "source_uri_enough": package_metrics["source_uri_count"] >= 5,
        "summary_metrics_match_cases": int(summary_metrics.get("regression_case_count", 0) or 0)
        == package_metrics["regression_case_count"],
        "summary_metrics_match_documents": int(summary_metrics.get("knowledge_document_count", 0) or 0)
        == package_metrics["knowledge_document_count"],
        "kb1_preview_can_apply": preview.get("can_apply") is True,
        "kb1_preview_create_count": int((preview.get("operation_counts") or {}).get("create", 0) or 0) >= 17,
        "kb1_import_can_apply": imported.get("can_apply") is True,
        "kb1_import_create_count": int((imported.get("operation_counts") or {}).get("create", 0) or 0) >= 17,
        "kb1_import_no_external_write": safety.get("external_write_performed") is False,
        "kb1_import_no_provider_call": safety.get("provider_call_performed") is False,
        "kb1_rollback_supported": safety.get("rollback_supported") is True,
        "kb1_rollback_done": rollback.get("rollback_status") == "rolled_back",
        "kb1_rollback_clean_documents": _int_value(rollback.get("active_document_count_after_rollback")) == 0,
        "kb1_rollback_clean_evals": _int_value(rollback.get("active_evaluation_set_count_after_rollback")) == 0,
    }
    blockers.extend([f"KB2 复测输入不满足：{name}" for name, passed in package_checks.items() if not passed])
    metrics = {key: value for key, value in package_metrics.items() if key != "cases"}
    return blockers, metrics, package_checks


def _build_signoff_template_rows(metrics: dict[str, Any]) -> list[dict[str, str]]:
    base_rows = [
        (
            "KB2-SIGNOFF-001",
            "知识范围",
            "业务对象覆盖",
            f"业务对象 {metrics['business_object_count']} 个，需要客户确认是否覆盖当前试点商品、服务和本地试点说明。",
            "业务负责人",
        ),
        (
            "KB2-SIGNOFF-002",
            "知识范围",
            "来源文档覆盖",
            f"来源文档 {metrics['knowledge_document_count']} 份、来源 URI {metrics['source_uri_count']} 个，需要客户确认来源资料可用于客服回答。",
            "业务负责人",
        ),
        (
            "KB2-SIGNOFF-003",
            "回答策略",
            "标准问答覆盖",
            "标准问答已进入对象知识卡；客户需确认答案是否符合实际商品和服务口径。",
            "客服负责人",
        ),
        (
            "KB2-SIGNOFF-004",
            "回答策略",
            "流程政策覆盖",
            "流程政策类知识已进入回归题；客户需确认售后、发货、知识更新流程是否正确。",
            "客服负责人",
        ),
        (
            "KB2-SIGNOFF-005",
            "风险边界",
            "禁用承诺覆盖",
            "禁用承诺类知识已进入复测；客户需确认不得承诺的表达是否完整。",
            "业务负责人",
        ),
        (
            "KB2-SIGNOFF-006",
            "风险边界",
            "转人工规则覆盖",
            f"转人工样本 {metrics['handoff_case_count']} 条；客户需确认高风险、投诉和责任类问题是否应转人工。",
            "客服负责人",
        ),
        (
            "KB2-SIGNOFF-007",
            "复测题库",
            "导入后回归题",
            f"回归题 {metrics['regression_case_count']} 条，其中自动回复候选 {metrics['auto_reply_case_count']} 条、转人工 {metrics['handoff_case_count']} 条。",
            "业务负责人",
        ),
        (
            "KB2-SIGNOFF-008",
            "系统边界",
            "真实外发关闭确认",
            "当前仍为本地受控试点，真实平台外发默认关闭；客户确认前不能启用真实外发。",
            "项目负责人",
        ),
        (
            "KB2-SIGNOFF-009",
            "系统边界",
            "导入与回滚证据",
            "KB1 已验证知识包预检、导入、查询和回滚；客户正式启用前仍需重新确认资料和备份。",
            "项目负责人",
        ),
    ]
    return [
        {
            "signoff_item_id": item_id,
            "section": section,
            "item_name": item_name,
            "evidence_summary": evidence_summary,
            "expected_reviewer": expected_reviewer,
            "review_status": "pending",
            "customer_comment": "",
            "confirmed_by": "",
            "confirmed_at": "",
            "needs_change": "",
            "not_formal_signoff": "true",
        }
        for item_id, section, item_name, evidence_summary, expected_reviewer in base_rows
    ]


def _validate_signoff_rows(rows: list[dict[str, str]]) -> tuple[list[str], dict[str, int]]:
    blockers: list[str] = []
    filled_confirmations = 0
    for row in rows:
        item_id = row.get("signoff_item_id", "unknown")
        if row.get("review_status") != "pending":
            blockers.append(f"{item_id} 签收模板必须保持 pending")
        if row.get("confirmed_by") or row.get("confirmed_at"):
            filled_confirmations += 1
            blockers.append(f"{item_id} 签收模板不得预填客户确认人或确认时间")
        if row.get("not_formal_signoff") != "true":
            blockers.append(f"{item_id} 必须保持 not_formal_signoff=true")
    return blockers, {
        "signoff_template_row_count": len(rows),
        "filled_customer_confirmation_count": filled_confirmations,
    }


def _write_retest_report(path: Path, result: dict[str, Any]) -> None:
    metrics = result["metrics"]
    lines = [
        "# H2W-KB2 客户专属知识包导入后复测报告",
        "",
        "## 结论",
        "",
        f"- 阶段状态：`{result['status']}`",
        f"- 复测报告就绪：`{str(result['readiness']['ready_for_post_import_retest_report']).lower()}`",
        f"- 客户签收模板就绪：`{str(result['readiness']['ready_for_customer_signoff_template']).lower()}`",
        f"- 正式客户签收就绪：`{str(result['readiness']['formal_customer_signoff_ready']).lower()}`",
        f"- 客户资料启用状态：`{str(result['readiness']['customer_specific_knowledge_ready']).lower()}`",
        "",
        "## 复测范围",
        "",
        "- 本报告基于 H2W-KB1 内部脱敏资料包与导入回滚证据生成。",
        "- 本报告只用于客户确认前的复测准备，不代表客户已经确认标准答案。",
        "- 当前未使用真实客户聊天原文、手机号、订单号、模型 provider 调用或真实平台外发。",
        "",
        "## 复测指标",
        "",
        f"- 业务对象：{metrics['business_object_count']}",
        f"- 对象知识卡：{metrics['object_knowledge_card_count']}",
        f"- 来源文档：{metrics['knowledge_document_count']}",
        f"- 来源 URI：{metrics['source_uri_count']}",
        f"- 回归题：{metrics['regression_case_count']}",
        f"- 自动回复候选：{metrics['auto_reply_case_count']}",
        f"- 转人工样本：{metrics['handoff_case_count']}",
        f"- 知识类型：{', '.join(metrics['knowledge_types'])}",
        "",
        "## 启用前客户需要确认",
        "",
        "1. 商品、服务、流程和禁用承诺是否符合实际业务。",
        "2. 哪些问题允许自动回复，哪些问题必须转人工。",
        "3. 标准答案是否需要调整，是否有新增活动、售后规则或渠道规则。",
        "4. 导入前是否完成本地备份，导入后是否完成回归复测。",
        "",
        "## 固定边界",
        "",
        "- `internal_rehearsal_not_customer_signoff=true`",
        "- `real_customer_data_used=false`",
        "- `provider_call_performed=false`",
        "- `real_platform_send_performed=false`",
        "- `formal_customer_signoff_performed=false`",
        "- `customer_specific_knowledge_ready=false`",
        "",
        "## 阻断项",
        "",
    ]
    lines.extend([f"- {item}" for item in result["blockers"]] or ["- 无"])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_stage_doc(path: Path, result: dict[str, Any]) -> None:
    lines = [
        "# H2W-KB2 客户专属知识包导入后复测与签收模板",
        "",
        "## 阶段定位",
        "",
        "H2W-KB2 只把 KB1 的客户专属知识包导入、查询、回滚证据整理成“复测报告”和“客户签收模板”。",
        "它不是正式客户签收，也不代表客户专属知识库已经正式启用。",
        "",
        "## 输出物",
        "",
        f"- 复测报告：`{result['evidence']['post_import_retest_report']['path']}`",
        f"- 签收模板：`{result['evidence']['signoff_template_csv']['path']}`",
        f"- 机器摘要：`{result['evidence']['summary_json']['path']}`",
        "",
        "## 验收结论",
        "",
        f"- 状态：`{result['status']}`",
        f"- 客户签收模板行数：{result['metrics']['signoff_template_row_count']}",
        f"- 已预填客户确认数：{result['metrics']['filled_customer_confirmation_count']}",
        f"- 正式客户签收：`{str(result['readiness']['formal_customer_signoff_ready']).lower()}`",
        f"- 真实外发：`{str(result['boundaries']['real_platform_send_performed']).lower()}`",
        "",
        "## 不可对外写成",
        "",
        "- 不能把客户确认、知识库启用或平台外发写成已经完成。",
        "- 不能把内部演练报告当作对外验收结论。",
        "- 不能把本地模板当作客户电子签章或合同签收。",
        "- 不能写成企业渠道真实上线。",
        "",
        "## 下一步",
        "",
        "- 让客户或内部业务负责人按模板逐项确认。",
        "- 有修订意见时先生成新版知识包，再重新预检、导入、回滚和复测。",
        "- 正式启用前仍需本地备份、回归复测、客户确认记录和真实外发专项授权。",
        "",
        "## 阻断项",
        "",
    ]
    lines.extend([f"- {item}" for item in result["blockers"]] or ["- 无"])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _text_overclaim_blockers(paths: list[Path]) -> list[str]:
    blockers: list[str] = []
    for path in paths:
        if not path.exists():
            blockers.append(f"输出文件缺失：{_display_path(path)}")
            continue
        text = path.read_text(encoding="utf-8")
        for phrase in OVERCLAIM_PHRASES:
            if phrase in text:
                blockers.append(f"{_display_path(path)} 出现越界表述：{phrase}")
    return blockers


def run_h2w_kb2_post_import_retest_and_signoff_template(
    *,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    doc_path: Path = DOC_PATH,
    kb1_summary: Path = KB1_SUMMARY,
    kb1_package: Path = KB1_PACKAGE,
    ops1_summary: Path = OPS1_SUMMARY,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    summary_path = output_dir / "summary.json"
    retest_report_path = output_dir / "post_import_retest_report.md"
    signoff_template_path = output_dir / "customer_knowledge_retest_signoff_template.csv"

    blockers: list[str] = []
    warnings: list[str] = []

    kb1_payload, kb1_blockers = _load_upstream_summary(
        kb1_summary,
        name="KB1",
        expected_status="ready_for_customer_specific_knowledge_package_rehearsal",
    )
    ops1_payload, ops1_blockers = _load_upstream_summary(
        ops1_summary,
        name="OPS1",
        expected_status="ready_for_after_sales_ops_handoff_rehearsal",
    )
    blockers.extend(kb1_blockers)
    blockers.extend(ops1_blockers)
    blockers.extend(_upstream_boundary_blockers(kb1_payload, name="KB1"))
    blockers.extend(_upstream_boundary_blockers(ops1_payload, name="OPS1"))

    if not kb1_package.exists():
        package = {}
        blockers.append(f"KB1 资料包缺失：{_display_path(kb1_package)}")
    else:
        try:
            package = _read_json(kb1_package)
        except json.JSONDecodeError:
            package = {}
            blockers.append(f"KB1 资料包不是有效 JSON：{_display_path(kb1_package)}")

    package_blockers, metrics, package_checks = _validate_package_and_kb1_summary(
        package=package,
        kb1_summary=kb1_payload,
    )
    blockers.extend(package_blockers)

    signoff_rows = _build_signoff_template_rows(metrics)
    signoff_blockers, signoff_metrics = _validate_signoff_rows(signoff_rows)
    blockers.extend(signoff_blockers)
    metrics.update(signoff_metrics)

    ready = not blockers
    status = "ready_for_customer_specific_knowledge_retest_template" if ready else "blocked"
    result = {
        "schema_version": "p3-06u-26h2w-kb2.post_import_retest_and_signoff_template.v1",
        "phase": PHASE,
        "status": status,
        "readiness": {
            "ready_for_post_import_retest_report": ready,
            "ready_for_customer_signoff_template": ready,
            "ready_for_customer_knowledge_review": ready,
            "customer_specific_knowledge_ready": False,
            "formal_customer_signoff_ready": False,
            "real_platform_send_ready": False,
        },
        "metrics": metrics,
        "checks": {
            "package": package_checks,
            "kb1_upstream_status": {
                "path": _display_path(kb1_summary),
                "expected": "ready_for_customer_specific_knowledge_package_rehearsal",
                "actual": kb1_payload.get("status"),
            },
            "ops1_upstream_status": {
                "path": _display_path(ops1_summary),
                "expected": "ready_for_after_sales_ops_handoff_rehearsal",
                "actual": ops1_payload.get("status"),
            },
        },
        "blockers": blockers,
        "warnings": warnings,
        "signoff_boundary": {
            "template_only": True,
            "customer_confirmed": False,
            "filled_customer_confirmation_count": metrics["filled_customer_confirmation_count"],
            "formal_contract_signoff_performed": False,
        },
        "boundaries": {
            "internal_rehearsal_not_customer_signoff": True,
            "real_customer_data_used": False,
            "provider_call_performed": False,
            "real_platform_send_performed": False,
            "external_platform_write_performed": False,
            "formal_customer_signoff_performed": False,
            "customer_specific_knowledge_ready": False,
            "enterprise_channel_scope_included": False,
        },
        "evidence": {
            "summary_json": {"path": _display_path(summary_path)},
            "post_import_retest_report": {"path": _display_path(retest_report_path)},
            "signoff_template_csv": {"path": _display_path(signoff_template_path)},
            "stage_doc": {"path": _display_path(doc_path)},
            "kb1_summary": {"path": _display_path(kb1_summary), "present": kb1_summary.exists()},
            "kb1_package": {"path": _display_path(kb1_package), "present": kb1_package.exists()},
            "ops1_summary": {"path": _display_path(ops1_summary), "present": ops1_summary.exists()},
        },
        "next_recommended_steps": [
            "客户或内部业务负责人按签收模板逐项确认资料范围、标准答案、禁用承诺和转人工规则。",
            "如出现修订意见，先生成新版知识包，再重新预检、导入、回滚和复测。",
            "正式启用前继续保持真实外发关闭，并另开官方渠道和客户签收专项。",
        ],
    }

    _write_csv(signoff_template_path, signoff_rows)
    _write_retest_report(retest_report_path, result)
    _write_stage_doc(doc_path, result)
    blockers.extend(_text_overclaim_blockers([retest_report_path, doc_path]))
    if blockers != result["blockers"]:
        result["blockers"] = blockers
        result["status"] = "blocked"
        result["readiness"]["ready_for_post_import_retest_report"] = False
        result["readiness"]["ready_for_customer_signoff_template"] = False
        result["readiness"]["ready_for_customer_knowledge_review"] = False
    _write_json(summary_path, result)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Run H2W-KB2 post-import retest and signoff-template gate.")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--kb1-summary", type=Path, default=KB1_SUMMARY)
    parser.add_argument("--kb1-package", type=Path, default=KB1_PACKAGE)
    parser.add_argument("--ops1-summary", type=Path, default=OPS1_SUMMARY)
    args = parser.parse_args()
    result = run_h2w_kb2_post_import_retest_and_signoff_template(
        output_dir=args.output_dir,
        kb1_summary=args.kb1_summary,
        kb1_package=args.kb1_package,
        ops1_summary=args.ops1_summary,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] != "blocked" else 1


if __name__ == "__main__":
    raise SystemExit(main())
