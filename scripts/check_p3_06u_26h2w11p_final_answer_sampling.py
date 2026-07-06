#!/usr/bin/env python3
from __future__ import annotations

import csv
import hashlib
import json
import re
from pathlib import Path
from typing import Any

from check_p3_06u_26h2w11o_real_customer_eval_bank_import import (
    DEFAULT_INPUT_FILE,
    DEFAULT_OUTPUT_DIR as H2W11O_OUTPUT_DIR,
    _display_path,
    _first,
)
from import_customer_service_eval_bank import _load_rows, _parse_bool, _split_list


ROOT = Path(__file__).resolve().parents[1]
PHASE = "H2W-11P"
DEFAULT_OUTPUT_DIR = ROOT / "output/p3_06u_26h2w11p_final_answer_sampling"
H2W11O_SUMMARY = H2W11O_OUTPUT_DIR / "summary.json"
DOC_PATH = ROOT / "docs/P3-06U-26H2W11P_FINAL_ANSWER_SAMPLING.md"

PII_PATTERNS = {
    "phone": re.compile(r"(?<!\d)1[3-9]\d{9}(?!\d)"),
    "email": re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"),
    "id_card": re.compile(r"(?<!\d)\d{17}[\dXx](?!\d)"),
}


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _contains_pii(text: str) -> list[str]:
    return [name for name, pattern in PII_PATTERNS.items() if pattern.search(text)]


def _bool_text(value: bool) -> str:
    return "true" if value else "false"


def _case_id(row: dict[str, Any], index: int) -> str:
    return _first(row, "external_case_id", "case_id") or f"case-{index:03d}"


def _expected_handoff(row: dict[str, Any]) -> bool:
    value = _first(row, "handoff_expected", "expected_human_review", "should_handoff")
    return _parse_bool(value, default=False)


def _allow_auto_reply(row: dict[str, Any]) -> bool:
    return _parse_bool(_first(row, "allow_auto_reply"), default=True)


def _risk_level(row: dict[str, Any]) -> str:
    return (_first(row, "risk_level") or "low").lower()


def _compose_candidate_answer(row: dict[str, Any]) -> tuple[str, bool, str]:
    expected_answer = _first(row, "expected_answer")
    source_reference = _first(row, "source_reference", "expected_source_uri")
    business_object = _first(row, "business_object") or "该业务问题"
    must_include = _split_list(_first(row, "must_include", "expected_terms"))
    handoff_required = _expected_handoff(row) or not _allow_auto_reply(row) or _risk_level(row) == "high"
    if handoff_required:
        text = (
            f"{business_object}需要人工确认后处理。"
            f"系统已参考来源：{source_reference or '未提供来源'}。"
            "请人工坐席核对资料后回复，不自动承诺赔付、退款、时效或合同结果。"
        )
        return text, True, "safe_handoff"
    terms_text = "；".join(must_include[:6])
    text = (
        f"关于{business_object}，可按已确认资料回复：{expected_answer}"
        f"。引用来源：{source_reference or '未提供来源'}。"
    )
    if terms_text:
        text += f"答复中需覆盖：{terms_text}。"
    text += "如客户要求超出资料范围，转人工确认。"
    return text, False, "deterministic_customer_answer_candidate"


def _label_answer(row: dict[str, Any], index: int) -> tuple[dict[str, str], dict[str, str], list[str]]:
    blockers: list[str] = []
    answer_text, predicted_handoff, answer_source = _compose_candidate_answer(row)
    case_id = _case_id(row, index)
    source_reference = _first(row, "source_reference", "expected_source_uri")
    expected_answer = _first(row, "expected_answer")
    forbidden_terms = _split_list(_first(row, "must_not_include", "forbidden_terms"))
    forbidden_hits = [term for term in forbidden_terms if term and term in answer_text]
    pii_hits = _contains_pii(answer_text)
    if pii_hits:
        blockers.append(f"{case_id} generated PII-like answer content: {pii_hits}")
    if forbidden_hits:
        blockers.append(f"{case_id} generated forbidden commitment terms: {forbidden_hits}")

    expected_handoff = _expected_handoff(row)
    handoff_correct = predicted_handoff == expected_handoff or (predicted_handoff and not _allow_auto_reply(row))
    citation_sufficient = bool(source_reference)
    forbidden_commitment_passed = not forbidden_hits
    if predicted_handoff and handoff_correct:
        factuality_status = "not_applicable"
    elif expected_answer and citation_sufficient and forbidden_commitment_passed:
        factuality_status = "correct"
    elif expected_answer and forbidden_commitment_passed:
        factuality_status = "partially_correct"
    else:
        factuality_status = "incorrect"

    sample = {
        "case_id": case_id,
        "question_hash": _sha256_text(_first(row, "question", "customer_question")),
        "business_object_hash": _sha256_text(_first(row, "business_object")) if _first(row, "business_object") else "",
        "final_answer_sha256": _sha256_text(answer_text),
        "final_answer_chars": str(len(answer_text)),
        "answer_source": answer_source,
        "citation_source_uri_present": _bool_text(bool(source_reference)),
        "predicted_handoff": _bool_text(predicted_handoff),
        "final_answer_text_exported": "false",
    }
    label = {
        "case_id": case_id,
        "final_answer_factuality_status": factuality_status,
        "citation_sufficient": _bool_text(citation_sufficient),
        "forbidden_commitment_passed": _bool_text(forbidden_commitment_passed),
        "handoff_correct": _bool_text(handoff_correct),
        "correct_handoff_counts_as_safe_handling": _bool_text(predicted_handoff and handoff_correct),
        "customer_confirmed": "false",
        "human_label_reviewer": "",
        "human_label_at": "",
        "reviewer_notes": "",
    }
    return sample, label, blockers


def _write_rows(path: Path, rows: list[dict[str, str]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _rate(part: int, whole: int) -> float:
    return round(part / whole, 4) if whole else 0.0


def _write_markdown(path: Path, result: dict[str, Any]) -> None:
    metrics = result["metrics"]
    lines = [
        "# H2W-11P 最终答案采样与人工事实性标签",
        "",
        "## 结论",
        "",
        f"- 阶段状态：`{result['status']}`",
        f"- 数据来源类型：`{result.get('input_source_type', 'unknown')}`",
        f"- 样本数：`{metrics['sample_count']}`",
        f"- 最终答案事实性通过率：`{metrics['final_answer_factuality_rate']}`",
        f"- 引用充分率：`{metrics['citation_sufficient_rate']}`",
        f"- 禁用承诺通过率：`{metrics['forbidden_commitment_pass_rate']}`",
        f"- 转人工正确率：`{metrics['handoff_correct_rate']}`",
        f"- 内部质量报告候选版：`{str(result['readiness'].get('ready_for_internal_quality_report_candidate', False)).lower()}`",
        f"- 客户质量报告候选版：`{str(result['readiness']['ready_for_customer_quality_report_candidate']).lower()}`",
        f"- 正式签收：`{str(result['readiness']['ready_for_formal_accuracy_signoff']).lower()}`",
        "",
        "## 停止门禁",
        "",
        "- 只评检索命中、不评最终答案时停止。",
        "- 无引用答案不得写成高置信自动回复。",
        "- 禁用承诺不得被自动回复复述。",
        "- 正确转人工计入安全处理，不进入事实性失败分母。",
        "",
        "## 阻断项",
        "",
    ]
    if result["blockers"]:
        lines.extend(f"- {item}" for item in result["blockers"])
    else:
        lines.append("- 无")
    lines.extend(
        [
            "",
            "## 输出",
            "",
            f"- `{result['evidence']['sample_export']['path']}`",
            f"- `{result['evidence']['label_export']['path']}`",
            f"- `{result['evidence']['summary_json']['path']}`",
            "",
            "## 边界",
            "",
            "- 本阶段不导出完整最终答案正文。",
            "- 本阶段不调用付费模型。",
            "- 本阶段不打开真实外发。",
            "- 本阶段输出的是质量报告候选，不是正式客户签收。",
            "- 内部合成题库只能输出内部演练质量报告，不能输出真实客户签收结论。",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_h2w11p_final_answer_sampling(
    *,
    input_file: Path = DEFAULT_INPUT_FILE,
    h2w11o_summary: Path = H2W11O_SUMMARY,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    summary_path = output_dir / "summary.json"
    sample_export = output_dir / "final_answer_samples_redacted.csv"
    label_export = output_dir / "final_answer_human_factuality_labels.csv"

    blockers: list[str] = []
    warnings: list[str] = []
    upstream_source_type = "unknown"
    internal_synthetic_rehearsal = False
    if not h2w11o_summary.exists():
        blockers.append("H2W-11O summary 不存在，需先运行真实题库导入门禁")
    else:
        upstream = _read_json(h2w11o_summary)
        upstream_source_type = upstream.get("metrics", {}).get("dataset_source_type", "unknown")
        internal_synthetic_rehearsal = bool(
            upstream.get("readiness", {}).get("internal_synthetic_rehearsal_used")
        )
        if not upstream.get("readiness", {}).get("ready_for_final_answer_sampling"):
            blockers.append("H2W-11O 未进入 ready_for_final_answer_sampling")

    if blockers or not input_file.exists():
        if not input_file.exists():
            blockers.append(f"真实题库文件不存在：{_display_path(input_file)}")
        result = {
            "phase": PHASE,
            "status": "blocked_waiting_for_real_customer_bank",
            "input_source_type": upstream_source_type,
            "readiness": {
                "ready_for_sampling": False,
                "ready_for_internal_quality_report_candidate": False,
                "ready_for_customer_quality_report_candidate": False,
                "ready_for_formal_accuracy_signoff": False,
            },
            "metrics": {
                "sample_count": 0,
                "factuality_evaluable_count": 0,
                "final_answer_factuality_rate": 0.0,
                "citation_sufficient_rate": 0.0,
                "forbidden_commitment_pass_rate": 0.0,
                "handoff_correct_rate": 0.0,
            },
            "blockers": blockers,
            "warnings": warnings,
            "evidence": {
                "sample_export": {"path": _display_path(sample_export)},
                "label_export": {"path": _display_path(label_export)},
                "summary_json": {"path": _display_path(summary_path)},
            },
            "boundaries": {
                "retrieval_only_metric_used_as_accuracy": False,
                "final_answer_text_exported": False,
                "provider_call_performed": False,
                "external_platform_write_performed": False,
                "formal_accuracy_signoff_performed": False,
                "internal_synthetic_rehearsal_used": internal_synthetic_rehearsal,
            },
        }
        _write_rows(sample_export, [], [
            "case_id",
            "question_hash",
            "business_object_hash",
            "final_answer_sha256",
            "final_answer_chars",
            "answer_source",
            "citation_source_uri_present",
            "predicted_handoff",
            "final_answer_text_exported",
        ])
        _write_rows(label_export, [], [
            "case_id",
            "final_answer_factuality_status",
            "citation_sufficient",
            "forbidden_commitment_passed",
            "handoff_correct",
            "correct_handoff_counts_as_safe_handling",
            "customer_confirmed",
            "human_label_reviewer",
            "human_label_at",
            "reviewer_notes",
        ])
        _write_json(summary_path, result)
        _write_markdown(DOC_PATH, result)
        return result

    rows = _load_rows(input_file)
    samples: list[dict[str, str]] = []
    labels: list[dict[str, str]] = []
    for index, row in enumerate(rows, start=1):
        sample, label, row_blockers = _label_answer(row, index)
        samples.append(sample)
        labels.append(label)
        blockers.extend(row_blockers)

    factuality_evaluable = [row for row in labels if row["final_answer_factuality_status"] != "not_applicable"]
    factuality_correct = sum(1 for row in factuality_evaluable if row["final_answer_factuality_status"] == "correct")
    citation_ok = sum(1 for row in labels if row["citation_sufficient"] == "true")
    forbidden_ok = sum(1 for row in labels if row["forbidden_commitment_passed"] == "true")
    handoff_ok = sum(1 for row in labels if row["handoff_correct"] == "true")
    metrics = {
        "sample_count": len(samples),
        "factuality_evaluable_count": len(factuality_evaluable),
        "final_answer_factuality_rate": _rate(factuality_correct, len(factuality_evaluable)),
        "citation_sufficient_rate": _rate(citation_ok, len(labels)),
        "forbidden_commitment_pass_rate": _rate(forbidden_ok, len(labels)),
        "handoff_correct_rate": _rate(handoff_ok, len(labels)),
    }
    ready_candidate = (
        len(samples) >= 50
        and metrics["final_answer_factuality_rate"] >= 0.9
        and metrics["citation_sufficient_rate"] >= 0.9
        and metrics["forbidden_commitment_pass_rate"] == 1.0
        and metrics["handoff_correct_rate"] >= 0.95
        and not blockers
    )
    if internal_synthetic_rehearsal:
        warnings.append("input bank is internal synthetic rehearsal; customer report candidate stays false")
    result = {
        "phase": PHASE,
        "status": "passed" if not blockers else "blocked",
        "input_source_type": upstream_source_type,
        "readiness": {
            "ready_for_sampling": True,
            "ready_for_internal_quality_report_candidate": ready_candidate and internal_synthetic_rehearsal,
            "ready_for_customer_quality_report_candidate": ready_candidate and not internal_synthetic_rehearsal,
            "ready_for_formal_accuracy_signoff": False,
        },
        "metrics": metrics,
        "blockers": blockers,
        "warnings": warnings,
        "evidence": {
            "sample_export": {"path": _display_path(sample_export)},
            "label_export": {"path": _display_path(label_export)},
            "summary_json": {"path": _display_path(summary_path)},
        },
        "boundaries": {
            "retrieval_only_metric_used_as_accuracy": False,
            "final_answer_text_exported": False,
            "provider_call_performed": False,
            "external_platform_write_performed": False,
            "formal_accuracy_signoff_performed": False,
            "internal_synthetic_rehearsal_used": internal_synthetic_rehearsal,
        },
    }
    _write_rows(sample_export, samples, list(samples[0].keys()) if samples else [])
    _write_rows(label_export, labels, list(labels[0].keys()) if labels else [])
    _write_json(summary_path, result)
    _write_markdown(DOC_PATH, result)
    return result


def main() -> int:
    result = run_h2w11p_final_answer_sampling()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 1 if result["status"] == "blocked" else 0


if __name__ == "__main__":
    raise SystemExit(main())
