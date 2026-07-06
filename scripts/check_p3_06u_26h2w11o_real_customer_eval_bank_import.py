#!/usr/bin/env python3
from __future__ import annotations

import csv
import hashlib
import json
import re
from pathlib import Path
from typing import Any

from import_customer_service_eval_bank import (
    _load_rows,
    _split_list,
    run_customer_service_eval_bank_import,
)


ROOT = Path(__file__).resolve().parents[1]
PHASE = "H2W-11O"
DEFAULT_INPUT_FILE = ROOT / "evals/p3_06u_26h2w11o_real_customer_eval_bank_received.csv"
DEFAULT_OUTPUT_DIR = ROOT / "output/p3_06u_26h2w11o_real_customer_eval_bank_import"
DOC_PATH = ROOT / "docs/P3-06U-26H2W11O_REAL_CUSTOMER_EVAL_BANK_IMPORT.md"

PII_PATTERNS = {
    "phone": re.compile(r"(?<!\d)1[3-9]\d{9}(?!\d)"),
    "email": re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"),
    "id_card": re.compile(r"(?<!\d)\d{17}[\dXx](?!\d)"),
}


def _display_path(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:24]


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _first(row: dict[str, Any], *keys: str) -> str:
    for key in keys:
        value = row.get(key)
        if value is not None and str(value).strip():
            return str(value).strip()
    return ""


def _has_pii(row: dict[str, Any]) -> list[str]:
    haystack = "\n".join(
        _first(row, field)
        for field in (
            "question",
            "customer_question",
            "expected_answer",
            "business_object",
            "source_reference",
            "annotation_notes",
        )
    )
    return [name for name, pattern in PII_PATTERNS.items() if pattern.search(haystack)]


def _has_handoff_label(row: dict[str, Any]) -> bool:
    return bool(_first(row, "handoff_expected", "expected_human_review", "should_handoff"))


def _dataset_source_type(row: dict[str, Any]) -> str:
    return (_first(row, "dataset_source_type", "source_type") or "unspecified").strip()


def _is_internal_synthetic_rehearsal(rows: list[dict[str, Any]]) -> bool:
    return bool(rows) and all(_dataset_source_type(row) == "internal_synthetic_rehearsal" for row in rows)


def _redacted_catalog(rows: list[dict[str, Any]]) -> list[dict[str, str]]:
    catalog: list[dict[str, str]] = []
    for index, row in enumerate(rows, start=1):
        question = _first(row, "question", "customer_question")
        expected_answer = _first(row, "expected_answer")
        business_object = _first(row, "business_object")
        source_reference = _first(row, "source_reference", "expected_source_uri")
        must_include = _split_list(_first(row, "must_include", "expected_terms"))
        must_not_include = _split_list(_first(row, "must_not_include", "forbidden_terms"))
        catalog.append(
            {
                "row_number": str(index),
                "external_case_id": _first(row, "external_case_id", "case_id") or f"row-{index}",
                "dataset_source_type": _dataset_source_type(row),
                "question_hash": _sha256_text(question),
                "expected_answer_hash": _sha256_text(expected_answer) if expected_answer else "",
                "business_object_hash": _sha256_text(business_object) if business_object else "",
                "risk_level": _first(row, "risk_level") or "unspecified",
                "must_include_count": str(len(must_include)),
                "must_not_include_count": str(len(must_not_include)),
                "source_reference_present": str(bool(source_reference)).lower(),
                "handoff_label_present": str(_has_handoff_label(row)).lower(),
                "sensitive_pattern_hits": "|".join(_has_pii(row)),
            }
        )
    return catalog


def _write_catalog(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "row_number",
        "external_case_id",
        "dataset_source_type",
        "question_hash",
        "expected_answer_hash",
        "business_object_hash",
        "risk_level",
        "must_include_count",
        "must_not_include_count",
        "source_reference_present",
        "handoff_label_present",
        "sensitive_pattern_hits",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _write_markdown(path: Path, result: dict[str, Any]) -> None:
    metrics = result["metrics"]
    readiness = result["readiness"]
    lines = [
        "# H2W-11O 真实 50-100 条脱敏题库导入",
        "",
        "## 结论",
        "",
        f"- 阶段状态：`{result['status']}`",
        f"- 输入文件：`{result['evidence']['input_file']['path']}`",
        f"- 数据来源类型：`{metrics.get('dataset_source_type', 'unspecified')}`",
        f"- 真实题库文件存在：`{str(readiness['real_customer_bank_file_present']).lower()}`",
        f"- 真实客户题库已确认：`{str(readiness.get('real_customer_bank_confirmed', False)).lower()}`",
        f"- 题目数量：`{metrics['row_count']}`",
        f"- 是否满足 50-100 条：`{str(readiness['sample_size_ready']).lower()}`",
        f"- 脱敏扫描通过：`{str(readiness['desensitization_ready']).lower()}`",
        f"- 可进入最终答案采样：`{str(readiness['ready_for_final_answer_sampling']).lower()}`",
        "",
        "## 停止门禁",
        "",
        "- 少于 50 条时只能写成题库准备中，不能写成准确率验收。",
        "- 不允许 demo 题库冒充真实题库。",
        "- 内部合成演练题库必须标记为 `internal_synthetic_rehearsal`，只能用于工程 rehearsal。",
        "- 原文必须脱敏，疑似手机号、邮箱、身份证会阻断。",
        "- 每条必须有期望答案和转人工标签。",
        "- 每条建议绑定业务对象、引用来源、必含词或禁用词。",
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
            f"- `{result['evidence']['summary_json']['path']}`",
            f"- `{result['evidence']['redacted_catalog']['path']}`",
            "",
            "## 边界",
            "",
            "- 本阶段不调用付费模型。",
            "- 本阶段不打开真实外发。",
            "- 本阶段不导出原始问题或完整期望答案。",
            "- 本阶段题库通过后也仍不是正式客户签收。",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_h2w11o_real_customer_eval_bank_import(
    *,
    input_file: Path = DEFAULT_INPUT_FILE,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    summary_path = output_dir / "summary.json"
    catalog_path = output_dir / "real_customer_eval_bank_catalog_redacted.csv"
    blockers: list[str] = []
    warnings: list[str] = []

    if not input_file.exists():
        result = {
            "phase": PHASE,
            "status": "waiting_for_real_customer_bank",
            "readiness": {
                "real_customer_bank_file_present": False,
                "real_customer_bank_confirmed": False,
                "internal_synthetic_rehearsal_used": False,
                "sample_size_ready": False,
                "desensitization_ready": False,
                "field_completeness_ready": False,
                "ready_for_final_answer_sampling": False,
            },
            "metrics": {
                "row_count": 0,
                "sensitive_row_count": 0,
                "expected_answer_rows": 0,
                "handoff_label_rows": 0,
                "business_object_rows": 0,
                "source_reference_rows": 0,
                "required_or_forbidden_term_rows": 0,
                "dataset_source_type": "missing",
            },
            "blockers": [
                f"真实脱敏题库文件不存在：{_display_path(input_file)}；不得用 demo 数据冒充真实题库"
            ],
            "warnings": warnings,
            "evidence": {
                "input_file": {"path": _display_path(input_file), "present": False, "sha256": ""},
                "summary_json": {"path": _display_path(summary_path)},
                "redacted_catalog": {"path": _display_path(catalog_path)},
            },
            "boundaries": {
                "demo_bank_used_as_real": False,
                "internal_synthetic_rehearsal_used": False,
                "raw_question_text_exported": False,
                "provider_call_performed": False,
                "external_platform_write_performed": False,
                "formal_accuracy_signoff_performed": False,
            },
        }
        _write_catalog(catalog_path, [])
        _write_json(summary_path, result)
        _write_markdown(DOC_PATH, result)
        return result

    rows = _load_rows(input_file)
    internal_synthetic_rehearsal = _is_internal_synthetic_rehearsal(rows)
    source_types = sorted({_dataset_source_type(row) for row in rows})
    if internal_synthetic_rehearsal:
        warnings.append("using internal synthetic rehearsal bank; this is not real customer evidence")
    catalog = _redacted_catalog(rows)
    _write_catalog(catalog_path, catalog)
    import_result = run_customer_service_eval_bank_import(
        input_path=input_file,
        name="H2W-11O 真实客户脱敏题库",
        description="真实 50-100 条脱敏问题的导入前门禁；不调用模型，不写外部平台。",
        create=False,
    )

    row_count = len(rows)
    sensitive_rows = [item for item in catalog if item["sensitive_pattern_hits"]]
    expected_answer_rows = sum(1 for row in rows if _first(row, "expected_answer"))
    handoff_label_rows = sum(1 for row in rows if _has_handoff_label(row))
    business_object_rows = sum(1 for row in rows if _first(row, "business_object"))
    source_reference_rows = sum(1 for row in rows if _first(row, "source_reference", "expected_source_uri"))
    required_or_forbidden_rows = sum(
        1
        for row in rows
        if _first(row, "must_include", "expected_terms") or _first(row, "must_not_include", "forbidden_terms")
    )

    if row_count < 50:
        blockers.append(f"题库只有 {row_count} 条，少于 50 条，只能标记为题库准备中")
    if row_count > 100:
        warnings.append(f"题库有 {row_count} 条，超过本轮 50-100 条窗口，建议拆批次验收")
    if sensitive_rows:
        blockers.append(f"脱敏扫描发现 {len(sensitive_rows)} 行疑似敏感信息")
    if expected_answer_rows != row_count:
        blockers.append("存在缺少 expected_answer 的题目")
    if handoff_label_rows != row_count:
        blockers.append("存在缺少 handoff_expected/expected_human_review 标签的题目")
    if import_result["status"] != "validated":
        blockers.extend(import_result.get("validation_errors") or [f"导入器状态异常：{import_result['status']}"])

    readiness = {
        "real_customer_bank_file_present": True,
        "real_customer_bank_confirmed": not internal_synthetic_rehearsal,
        "internal_synthetic_rehearsal_used": internal_synthetic_rehearsal,
        "sample_size_ready": 50 <= row_count <= 100,
        "desensitization_ready": not sensitive_rows,
        "field_completeness_ready": expected_answer_rows == row_count and handoff_label_rows == row_count,
        "ready_for_final_answer_sampling": not blockers and 50 <= row_count <= 100,
    }
    metrics = {
        "row_count": row_count,
        "sensitive_row_count": len(sensitive_rows),
        "expected_answer_rows": expected_answer_rows,
        "handoff_label_rows": handoff_label_rows,
        "business_object_rows": business_object_rows,
        "source_reference_rows": source_reference_rows,
        "required_or_forbidden_term_rows": required_or_forbidden_rows,
        "risk_level_counts": import_result.get("summary", {}).get("risk_level_counts", {}),
        "business_object_coverage_rate": round(business_object_rows / row_count, 4) if row_count else 0,
        "source_reference_coverage_rate": round(source_reference_rows / row_count, 4) if row_count else 0,
        "term_rule_coverage_rate": round(required_or_forbidden_rows / row_count, 4) if row_count else 0,
        "dataset_source_type": "internal_synthetic_rehearsal"
        if internal_synthetic_rehearsal
        else ",".join(source_types),
        "internal_synthetic_rehearsal_rows": row_count if internal_synthetic_rehearsal else 0,
    }
    result = {
        "phase": PHASE,
        "status": "passed_internal_rehearsal"
        if readiness["ready_for_final_answer_sampling"] and internal_synthetic_rehearsal
        else "passed" if readiness["ready_for_final_answer_sampling"] else "blocked",
        "readiness": readiness,
        "metrics": metrics,
        "blockers": blockers,
        "warnings": warnings,
        "evidence": {
            "input_file": {
                "path": _display_path(input_file),
                "present": True,
                "sha256": _sha256_file(input_file),
            },
            "summary_json": {"path": _display_path(summary_path)},
            "redacted_catalog": {"path": _display_path(catalog_path)},
        },
        "boundaries": {
            "demo_bank_used_as_real": False,
            "internal_synthetic_rehearsal_used": internal_synthetic_rehearsal,
            "raw_question_text_exported": False,
            "provider_call_performed": False,
            "external_platform_write_performed": False,
            "formal_accuracy_signoff_performed": False,
        },
    }
    _write_json(summary_path, result)
    _write_markdown(DOC_PATH, result)
    return result


def main() -> int:
    result = run_h2w11o_real_customer_eval_bank_import()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 1 if result["status"] == "blocked" else 0


if __name__ == "__main__":
    raise SystemExit(main())
