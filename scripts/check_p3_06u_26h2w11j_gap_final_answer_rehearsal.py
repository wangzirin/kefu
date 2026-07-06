#!/usr/bin/env python3
from __future__ import annotations

import csv
import hashlib
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_DIR = ROOT / "output/p3_06u_26h2w11j_gap_final_answer_rehearsal"
H2W11I_SUMMARY = ROOT / "output/p3_06u_26h2w11i_standard_answer_gap_eval_plan/summary.json"
GAP_EVAL_CASES = ROOT / "evals/p3_06u_26h2w11i_standard_answer_gap_eval_cases.csv"
GAP_LABEL_PLAN = ROOT / "evals/p3_06u_26h2w11i_standard_answer_gap_label_plan.csv"
LABEL_EXPORT = DEFAULT_OUTPUT_DIR / "gap_final_answer_labels.csv"
SAMPLE_EXPORT = DEFAULT_OUTPUT_DIR / "gap_final_answer_samples_redacted.csv"
DOC_PATH = ROOT / "docs/P3-06U-26H2W11J_GAP_FINAL_ANSWER_REHEARSAL.md"
PRODUCT_PLAN_PATH = ROOT / "docs/PRODUCTIZATION_MASTER_PLAN_LITE_AND_STANDARD.md"
NETWORK_PLAN_PATH = ROOT / "docs/P3-06U-26H2W_NETWORKED_ENGINEERING_MASTER_PLAN.md"
README_PATH = ROOT / "README.md"

PII_PATTERNS = {
    "phone": re.compile(r"(?<!\d)1[3-9]\d{9}(?!\d)"),
    "email": re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"),
    "id_card": re.compile(r"(?<!\d)\d{17}[\dXx](?!\d)"),
}


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _read_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def _write_rows(path: Path, rows: list[dict[str, str]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _display_path(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def _split_multi(value: str) -> list[str]:
    return [item.strip() for item in re.split(r"[;；|、,，]", value or "") if item.strip()]


def _bool(value: str) -> bool:
    return str(value).strip().lower() == "true"


def _bool_text(value: bool) -> str:
    return "true" if value else "false"


def _redact_forbidden(text: str, forbidden_terms: list[str]) -> str:
    result = text
    replacements = {
        "直接改数据库": "绕过知识维护流程",
        "不用复测": "跳过启用前复测",
        "马上赔偿": "越权赔付承诺",
        "百分百退款": "绝对化退款承诺",
        "我们全责": "责任归属承诺",
        "永久免费": "长期免费承诺",
        "无限服务": "无限量服务承诺",
        "无限调用": "无限量调用承诺",
        "不计成本": "忽略成本约束",
        "凭感觉回答": "无依据回答",
        "无需依据": "无来源依据",
        "正式签收已完成": "正式签收完成承诺",
        "生产上线已完成": "生产上线完成承诺",
    }
    for term in sorted({term for term in forbidden_terms if term}, key=len, reverse=True):
        result = result.replace(term, replacements.get(term, "越界承诺"))
    return result


def _draft_text_for_case(row: dict[str, str]) -> tuple[str, str, bool]:
    required_terms = _split_multi(row.get("required_terms", ""))
    forbidden_terms = _split_multi(row.get("forbidden_terms", ""))
    source_title = row.get("expected_document_title", "").strip()
    business_object = row.get("business_object", "").strip()
    should_handoff = _bool(row.get("should_handoff", ""))

    if should_handoff:
        text = (
            f"这类问题涉及{business_object}的人工判断，需要转人工处理。"
            f"处理前应核对{source_title}，重点确认{'、'.join(required_terms)}，"
            "并按受控试点边界记录处理证据。"
        )
        return _redact_forbidden(text, forbidden_terms), "handoff_gate", True

    text = (
        f"关于{business_object}，可以按{source_title}回答。"
        f"先确认{'、'.join(required_terms)}，再给出当前可执行的处理建议；"
        "资料不足、政策边界不清或客户要求越权承诺时，转人工复核。"
    )
    return _redact_forbidden(text, forbidden_terms), "local_deterministic_rehearsal", False


def _contains_pii(text: str) -> list[str]:
    return [name for name, pattern in PII_PATTERNS.items() if pattern.search(text)]


def _label_case(row: dict[str, str], plan_by_id: dict[str, dict[str, str]]) -> tuple[dict[str, str], dict[str, str], list[str]]:
    blockers: list[str] = []
    gap_case_id = row["gap_case_id"]
    plan = plan_by_id.get(gap_case_id)
    if not plan:
        blockers.append(f"{gap_case_id} missing label plan")
        plan = {}

    draft_text, answer_source, predicted_handoff = _draft_text_for_case(row)
    required_terms = _split_multi(row.get("required_terms", ""))
    forbidden_terms = _split_multi(row.get("forbidden_terms", ""))
    required_terms_found = all(term in draft_text for term in required_terms)
    forbidden_hits = [term for term in forbidden_terms if term and term in draft_text]
    citation_sufficient = bool(row.get("expected_source_uri")) and _bool(row.get("required_citation", "true"))
    expected_handoff = _bool(row.get("should_handoff", ""))
    handoff_correct = expected_handoff == predicted_handoff
    forbidden_commitment_passed = not forbidden_hits

    if expected_handoff and handoff_correct and forbidden_commitment_passed:
        factuality_status = "not_applicable"
    elif required_terms_found and citation_sufficient and forbidden_commitment_passed and handoff_correct:
        factuality_status = "correct"
    elif citation_sufficient and forbidden_commitment_passed:
        factuality_status = "partially_correct"
    else:
        factuality_status = "incorrect"

    pii = _contains_pii(draft_text)
    if pii:
        blockers.append(f"{gap_case_id} generated PII-like draft: {pii}")
    if forbidden_hits:
        blockers.append(f"{gap_case_id} generated forbidden commitment terms: {forbidden_hits}")
    if _bool(row.get("customer_confirmed", "")):
        blockers.append(f"{gap_case_id} must not be customer_confirmed before real customer confirmation")
    if plan.get("final_answer_text_must_not_be_exported") != "true":
        blockers.append(f"{gap_case_id} label plan must forbid exporting final answer text")

    sample = {
        "gap_case_id": gap_case_id,
        "source_standard_case_id": row.get("source_standard_case_id", ""),
        "source_channel": row.get("source_channel", ""),
        "customer_scenario": row.get("customer_scenario", ""),
        "business_object": row.get("business_object", ""),
        "answer_source": answer_source,
        "final_answer_sha256": _sha256_text(draft_text),
        "final_answer_chars": str(len(draft_text)),
        "citation_uris": row.get("expected_source_uri", ""),
        "required_terms_found": _bool_text(required_terms_found),
        "predicted_handoff": _bool_text(predicted_handoff),
        "final_answer_text_exported": "false",
    }
    label = {
        "gap_case_id": gap_case_id,
        "source_standard_case_id": row.get("source_standard_case_id", ""),
        "expected_source_uri": row.get("expected_source_uri", ""),
        "final_answer_source": answer_source,
        "final_answer_text": "",
        "final_answer_factuality_status": factuality_status,
        "citation_sufficient": _bool_text(citation_sufficient),
        "forbidden_commitment_passed": _bool_text(forbidden_commitment_passed),
        "handoff_correct": _bool_text(handoff_correct),
        "required_terms_found": _bool_text(required_terms_found),
        "customer_confirmed": row.get("customer_confirmed", "false"),
        "reviewer_notes": "",
    }
    return sample, label, blockers


def _boundaries() -> dict[str, bool]:
    return {
        "provider_call_performed": False,
        "external_platform_write_performed": False,
        "real_platform_send_performed": False,
        "formal_customer_signoff_performed": False,
        "electronic_signature_performed": False,
        "real_customer_data_used": False,
        "final_answer_text_exported": False,
        "gap_final_answer_rehearsal_performed": True,
        "ready_for_formal_accuracy_signoff": False,
    }


def _write_report(path: Path, result: dict[str, Any]) -> None:
    metrics = result["metrics"]
    lines = [
        "# H2W-11J 缺口样本最终答案 rehearsal",
        "",
        "## 结论",
        "",
        f"- 门禁状态：{result['status']}",
        f"- 缺口样本数：{metrics['case_count']}",
        f"- 标签样本数：{metrics['label_count']}",
        f"- 自动回复样本事实性通过率：{metrics['auto_reply_factuality_rate']}",
        f"- 引用充分率：{metrics['citation_sufficient_rate']}",
        f"- 禁用承诺通过率：{metrics['forbidden_commitment_pass_rate']}",
        f"- 转人工正确率：{metrics['handoff_correct_rate']}",
        f"- 正式准确率签收：{'可进入' if result['boundaries']['ready_for_formal_accuracy_signoff'] else '不可进入'}",
        "",
        "## 标签分布",
        "",
        f"- final_answer_factuality_status：`{metrics['factuality_status_counts']}`",
        "",
        "## 输出文件",
        "",
        f"- `{result['evidence']['sample_export']['path']}`",
        f"- `{result['evidence']['label_export']['path']}`",
        "",
        "## 边界",
        "",
        "- 本轮是本地确定性 rehearsal，不调用真实模型。",
        "- 本轮不打开真实外发，不连接真实平台。",
        "- 本轮导出文件不包含完整最终答案正文。",
        "- 本轮不是正式客户准确率签收。",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_h2w11j_gap_final_answer_rehearsal_gate(
    *,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    sample_export_path: Path | None = None,
    label_export_path: Path | None = None,
) -> dict[str, Any]:
    blockers: list[str] = []
    warnings: list[str] = []
    sample_export = sample_export_path or output_dir / "gap_final_answer_samples_redacted.csv"
    label_export = label_export_path or output_dir / "gap_final_answer_labels.csv"

    required_files = [
        H2W11I_SUMMARY,
        GAP_EVAL_CASES,
        GAP_LABEL_PLAN,
        DOC_PATH,
        PRODUCT_PLAN_PATH,
        NETWORK_PLAN_PATH,
        README_PATH,
    ]
    for path in required_files:
        if not path.exists():
            blockers.append(f"required file missing: {_display_path(path)}")

    if blockers:
        result = {
            "phase": "H2W-11J",
            "status": "blocked",
            "blockers": blockers,
            "warnings": warnings,
            "boundaries": _boundaries(),
        }
        _write_json(output_dir / "summary.json", result)
        return result

    upstream = _read_json(H2W11I_SUMMARY)
    cases = _read_rows(GAP_EVAL_CASES)
    label_plan = _read_rows(GAP_LABEL_PLAN)
    plan_by_id = {row["gap_case_id"]: row for row in label_plan}

    if upstream.get("status") != "passed":
        blockers.append("H2W-11I must pass before H2W-11J")
    if upstream.get("coverage", {}).get("ready_for_next_final_answer_eval_run") is not True:
        blockers.append("H2W-11I must mark ready_for_next_final_answer_eval_run=true before rehearsal")
    if upstream.get("coverage", {}).get("ready_for_formal_accuracy_signoff") is not False:
        blockers.append("H2W-11I must keep formal accuracy signoff false")
    if len(cases) < 1:
        blockers.append("gap eval cases are empty")
    if len(label_plan) != len(cases):
        blockers.append("label plan row count must match gap case row count")

    samples: list[dict[str, str]] = []
    labels: list[dict[str, str]] = []
    for row in cases:
        sample, label, row_blockers = _label_case(row, plan_by_id)
        samples.append(sample)
        labels.append(label)
        blockers.extend(row_blockers)

    sample_fields = [
        "gap_case_id",
        "source_standard_case_id",
        "source_channel",
        "customer_scenario",
        "business_object",
        "answer_source",
        "final_answer_sha256",
        "final_answer_chars",
        "citation_uris",
        "required_terms_found",
        "predicted_handoff",
        "final_answer_text_exported",
    ]
    label_fields = [
        "gap_case_id",
        "source_standard_case_id",
        "expected_source_uri",
        "final_answer_source",
        "final_answer_text",
        "final_answer_factuality_status",
        "citation_sufficient",
        "forbidden_commitment_passed",
        "handoff_correct",
        "required_terms_found",
        "customer_confirmed",
        "reviewer_notes",
    ]
    _write_rows(sample_export, samples, sample_fields)
    _write_rows(label_export, labels, label_fields)

    exported_label_rows = _read_rows(label_export)
    if any((row.get("final_answer_text") or "").strip() for row in exported_label_rows):
        blockers.append("final_answer_text must remain blank in label export")

    factuality_counts = Counter(row["final_answer_factuality_status"] for row in labels)
    auto_labels = [row for row in labels if row["final_answer_factuality_status"] != "not_applicable"]
    auto_correct = [row for row in auto_labels if row["final_answer_factuality_status"] == "correct"]
    citation_true = [row for row in labels if row["citation_sufficient"] == "true"]
    forbidden_true = [row for row in labels if row["forbidden_commitment_passed"] == "true"]
    handoff_true = [row for row in labels if row["handoff_correct"] == "true"]
    customer_confirmed_true = [row for row in labels if row["customer_confirmed"] == "true"]
    if customer_confirmed_true:
        blockers.append("customer_confirmed must remain false for H2W-11J rehearsal")

    metrics = {
        "case_count": len(cases),
        "sample_count": len(samples),
        "label_count": len(labels),
        "auto_reply_label_count": len(auto_labels),
        "handoff_not_applicable_count": factuality_counts.get("not_applicable", 0),
        "auto_reply_factuality_rate": round(len(auto_correct) / len(auto_labels), 4) if auto_labels else 1.0,
        "citation_sufficient_rate": round(len(citation_true) / len(labels), 4) if labels else 0.0,
        "forbidden_commitment_pass_rate": round(len(forbidden_true) / len(labels), 4) if labels else 0.0,
        "handoff_correct_rate": round(len(handoff_true) / len(labels), 4) if labels else 0.0,
        "factuality_status_counts": {key: factuality_counts[key] for key in sorted(factuality_counts)},
        "ready_for_gap_quality_report_review": len(blockers) == 0,
        "ready_for_formal_accuracy_signoff": False,
    }
    if metrics["auto_reply_factuality_rate"] < 1.0:
        warnings.append("some auto reply rehearsal labels are not fully correct")
    if metrics["citation_sufficient_rate"] < 1.0:
        warnings.append("some gap rehearsal labels lack sufficient citation")
    if metrics["forbidden_commitment_pass_rate"] < 1.0:
        warnings.append("some gap rehearsal labels contain forbidden commitments")
    if metrics["handoff_correct_rate"] < 1.0:
        warnings.append("some gap rehearsal labels have wrong handoff decisions")

    evidence = {
        "upstream_h2w11i_summary": {
            "path": _display_path(H2W11I_SUMMARY),
            "sha256": _sha256_file(H2W11I_SUMMARY),
        },
        "sample_export": {
            "path": _display_path(sample_export),
            "sha256": _sha256_file(sample_export),
        },
        "label_export": {
            "path": _display_path(label_export),
            "sha256": _sha256_file(label_export),
        },
    }
    result = {
        "phase": "H2W-11J",
        "status": "passed" if not blockers else "blocked",
        "blockers": blockers,
        "warnings": warnings,
        "metrics": metrics,
        "evidence": evidence,
        "boundaries": _boundaries(),
        "next_actions": [
            "把 H2W-11J 缺口 rehearsal 汇入客户质量报告确认页，但继续标记为本地演练。",
            "若需要正式准确率签收，必须补客户确认标准答案、真实客户题库、线上回执和正式报告签收。",
            "真实 IM 和官方渠道外发继续另开授权专项。",
        ],
    }
    _write_json(output_dir / "summary.json", result)
    _write_report(output_dir / "gap_final_answer_rehearsal_report.md", result)
    return result


def main() -> int:
    result = run_h2w11j_gap_final_answer_rehearsal_gate()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
