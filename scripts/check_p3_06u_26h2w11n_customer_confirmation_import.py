#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from check_p3_06u_26h2w11m_customer_confirmation_import_gate import (
    DEFAULT_RETURN_FILE,
    H2W11L_PACK,
    RETURN_TEMPLATE,
    _display_path,
    _read_rows,
    _sha256_file,
    run_h2w11m_customer_confirmation_import_gate,
)


ROOT = Path(__file__).resolve().parents[1]
PHASE = "H2W-11N"
DEFAULT_OUTPUT_DIR = ROOT / "output/p3_06u_26h2w11n_customer_confirmation_import"
DOC_PATH = ROOT / "docs/P3-06U-26H2W11N_CUSTOMER_CONFIRMATION_IMPORT.md"


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _write_markdown(path: Path, result: dict[str, Any]) -> None:
    readiness = result["readiness"]
    metrics = result["metrics"]
    lines = [
        "# H2W-11N 客户确认结果导入实战",
        "",
        "## 结论",
        "",
        f"- 阶段状态：`{result['status']}`",
        f"- 客户回传文件：`{result['evidence']['return_file']['path']}`",
        f"- 回传文件存在：`{str(readiness['customer_return_file_present']).lower()}`",
        f"- 客户确认条目：`{metrics.get('customer_confirmed_item_count', 0)}`",
        f"- 内部演练确认条目：`{metrics.get('internal_rehearsal_item_count', 0)}`",
        f"- 修订条目：`{metrics.get('revise_item_count', 0)}`",
        f"- 拒绝条目：`{metrics.get('reject_item_count', 0)}`",
        f"- 下一版标准答案包准备：`{str(readiness['ready_for_next_standard_answer_pack']).lower()}`",
        f"- 正式准确率签收：`{str(readiness['ready_for_formal_accuracy_signoff']).lower()}`",
        "",
        "## 停止门禁",
        "",
        "- 没有真实客户回传文件时，只能生成等待回传报告。",
        "- 客户回传不得直接改标准答案正文、必含词、禁用词或来源 URI。",
        "- 已确认行必须包含确认人、角色和 ISO 格式确认时间。",
        "- 修订或拒绝行必须写明修订意见。",
        "- 疑似手机号、邮箱、身份证等敏感信息会阻断导入。",
        "",
        "## 当前阻断项",
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
            f"- `{result['evidence']['revision_items']['path']}`",
            f"- `{result['evidence']['rejected_items']['path']}`",
            "",
            "## 边界",
            "",
        "- 本阶段不伪造客户确认。",
        "- 内部演练确认只能用于工程链路验证，不等于真实客户确认。",
        "- 本阶段不修改客户标准答案包。",
            "- 本阶段不等于正式客户准确率签收。",
            "- 真实外发继续关闭。",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_rows(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if rows:
        fieldnames = list(rows[0].keys())
    else:
        fieldnames = ["confirmation_item_id", "customer_decision", "customer_revision_request"]
    import csv

    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def run_h2w11n_customer_confirmation_import(
    *,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    return_file_path: Path = DEFAULT_RETURN_FILE,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    summary_path = output_dir / "summary.json"
    revision_items_path = output_dir / "customer_revision_items.csv"
    rejected_items_path = output_dir / "customer_rejected_items.csv"

    h2w11m_output = output_dir / "h2w11m_gate"
    gate = run_h2w11m_customer_confirmation_import_gate(
        output_dir=h2w11m_output,
        return_template_path=RETURN_TEMPLATE,
        return_file_path=return_file_path,
    )

    blockers: list[str] = []
    warnings = list(gate.get("warnings", []))
    status = "passed"
    if not return_file_path.exists():
        status = "waiting_for_customer_return"
        blockers.append(
            f"真实客户确认回传文件不存在：{_display_path(return_file_path)}；不得标记客户确认完成"
        )
    elif gate.get("status") != "passed":
        status = "blocked"
        blockers.extend(gate.get("blockers", []))
    elif not gate["readiness"]["ready_for_confirmed_standard_answer_import"]:
        status = "waiting_for_customer_revision"
        blockers.extend(gate.get("blockers", []))
        if not blockers:
            blockers.append("客户回传包含 pending、revise 或 reject 项，需要先生成下一版标准答案包")

    internal_rehearsal_used = bool(gate.get("readiness", {}).get("internal_rehearsal_confirmation_used"))
    if status == "passed" and internal_rehearsal_used:
        status = "passed_internal_rehearsal"

    revision_rows: list[dict[str, str]] = []
    rejected_rows: list[dict[str, str]] = []
    return_sha256 = ""
    if return_file_path.exists():
        return_sha256 = _sha256_file(return_file_path)
        for row in _read_rows(return_file_path):
            decision = (row.get("customer_decision") or "").strip().lower()
            if decision == "revise":
                revision_rows.append(row)
            elif decision == "reject":
                rejected_rows.append(row)

    _write_rows(revision_items_path, revision_rows)
    _write_rows(rejected_items_path, rejected_rows)

    metrics = dict(gate.get("metrics", {}))
    metrics.update(
        {
            "revision_item_export_count": len(revision_rows),
            "rejected_item_export_count": len(rejected_rows),
        }
    )
    readiness = {
        "customer_return_file_present": return_file_path.exists(),
        "internal_rehearsal_confirmation_used": internal_rehearsal_used,
        "real_customer_confirmation_performed": bool(
            gate.get("readiness", {}).get("real_customer_confirmation_performed")
        ),
        "ready_for_confirmed_standard_answer_import": bool(
            gate["readiness"].get("ready_for_confirmed_standard_answer_import")
        ),
        "ready_for_next_standard_answer_pack": bool(revision_rows or rejected_rows),
        "ready_for_formal_accuracy_signoff": False,
    }
    result = {
        "phase": PHASE,
        "status": status,
        "readiness": readiness,
        "metrics": metrics,
        "blockers": blockers,
        "warnings": warnings,
        "evidence": {
            "confirmation_pack": {
                "path": _display_path(H2W11L_PACK),
                "sha256": _sha256_file(H2W11L_PACK) if H2W11L_PACK.exists() else "",
            },
            "return_template": {
                "path": _display_path(RETURN_TEMPLATE),
                "sha256": _sha256_file(RETURN_TEMPLATE) if RETURN_TEMPLATE.exists() else "",
            },
            "return_file": {
                "path": _display_path(return_file_path),
                "present": return_file_path.exists(),
                "sha256": return_sha256,
            },
            "summary_json": {"path": _display_path(summary_path)},
            "revision_items": {"path": _display_path(revision_items_path)},
            "rejected_items": {"path": _display_path(rejected_items_path)},
            "upstream_h2w11m_summary": {
                "path": _display_path(h2w11m_output / "summary.json"),
                "status": gate.get("status"),
            },
        },
        "boundaries": {
            "customer_confirmation_fabricated": False,
            "internal_rehearsal_confirmation_used": internal_rehearsal_used,
            "standard_answer_directly_modified": False,
            "formal_accuracy_signoff_performed": False,
            "real_platform_send_performed": False,
            "paid_model_call_performed": False,
        },
    }
    _write_json(summary_path, result)
    _write_markdown(DOC_PATH, result)
    return result


def main() -> int:
    result = run_h2w11n_customer_confirmation_import()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 1 if result["status"] == "blocked" else 0


if __name__ == "__main__":
    raise SystemExit(main())
