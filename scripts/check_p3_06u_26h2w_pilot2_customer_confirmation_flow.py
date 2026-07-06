#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import re
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PHASE = "H2W-PILOT2"
SCHEMA_VERSION = "p3-06u-26h2w-pilot2.customer_confirmation_flow_gate.v1"
DEFAULT_OUTPUT_DIR = ROOT / "output/p3_06u_26h2w_pilot2_customer_confirmation_flow"
DOC_PATH = ROOT / "docs/P3-06U-26H2W_PILOT2_CUSTOMER_CONFIRMATION_FLOW.md"
TEMPLATE_CSV = ROOT / "output/p3_06u_26h2w_kb2_post_import_retest_and_signoff_template/customer_knowledge_retest_signoff_template.csv"

SECRET_PATTERNS = [
    re.compile(r"(?i)(api[_-]?key|access[_-]?token|secret|password)\s*[:=]\s*[A-Za-z0-9_\-]{10,}"),
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
]


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _display_path(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def _read_rows(path: Path) -> tuple[list[dict[str, str]], list[str]]:
    if not path.exists():
        return [], [f"确认模板缺失：{_display_path(path)}"]
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)
    if not rows:
        return [], [f"确认模板为空：{_display_path(path)}"]
    return rows, []


def _value(row: dict[str, str], *names: str) -> str:
    normalized = {key.strip().lower(): (value or "").strip() for key, value in row.items() if key is not None}
    for name in names:
        found = normalized.get(name.lower())
        if found is not None:
            return found
    return ""


def _scan_sensitive(row: dict[str, str], row_number: int) -> list[str]:
    text = " ".join(str(value or "") for value in row.values())
    return [f"第 {row_number} 行包含疑似密钥或密码形态" for pattern in SECRET_PATTERNS if pattern.search(text)]


def _classify_status(value: str) -> str:
    normalized = value.strip().lower()
    if normalized in {"confirmed", "accepted", "确认通过", "已确认", "通过"}:
        return "confirmed"
    if normalized in {"accepted_with_notes", "confirmed_with_notes", "有备注通过", "带备注确认"}:
        return "accepted_with_notes"
    if normalized in {"needs_revision", "need_revision", "需修订", "需要修订", "需修改"}:
        return "needs_revision"
    if normalized in {"rejected", "reject", "已拒绝", "拒绝"}:
        return "rejected"
    if normalized in {"", "pending", "待确认", "未确认"}:
        return "pending"
    return "unknown"


def _write_markdown(path: Path, result: dict[str, Any]) -> None:
    lines = [
        "# H2W-PILOT2 客户知识确认流程",
        "",
        "## 结论",
        "",
        f"- 阶段状态：`{result['status']}`",
        f"- 表格行数：{result['metrics']['total_rows']}",
        f"- 待确认：{result['metrics']['pending_count']}",
        f"- 需修订：{result['metrics']['needs_revision_count']}",
        f"- 已拒绝：{result['metrics']['rejected_count']}",
        "",
        "## 边界",
        "",
        "- 无真实回填文件时只能显示等待客户确认。",
        "- 系统不得替客户预填确认人、确认时间或同意状态。",
        "- 该流程不等于正式客户签收。",
    ]
    if result["blockers"]:
        lines.extend(["", "## 阻断项", ""])
        lines.extend(f"- {item}" for item in result["blockers"])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_h2w_pilot2_customer_confirmation_flow(
    *,
    csv_path: Path = TEMPLATE_CSV,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    doc_path: Path = DOC_PATH,
) -> dict[str, Any]:
    rows, blockers = _read_rows(csv_path)
    required_columns = {"signoff_item_id", "section", "item_name", "review_status", "confirmed_by", "confirmed_at"}
    if rows:
        actual_columns = {key.strip() for key in rows[0].keys() if key is not None}
        missing_columns = sorted(required_columns - actual_columns)
        blockers.extend(f"确认表缺少字段：{item}" for item in missing_columns)

    pending_count = 0
    confirmed_count = 0
    needs_revision_count = 0
    rejected_count = 0
    accepted_with_notes_count = 0
    for index, row in enumerate(rows, start=2):
        status_bucket = _classify_status(_value(row, "review_status", "status"))
        if status_bucket == "pending":
            pending_count += 1
        elif status_bucket == "confirmed":
            confirmed_count += 1
        elif status_bucket == "accepted_with_notes":
            accepted_with_notes_count += 1
        elif status_bucket == "needs_revision":
            needs_revision_count += 1
        elif status_bucket == "rejected":
            rejected_count += 1
        else:
            blockers.append(f"第 {index} 行确认状态无法识别")
        if status_bucket in {"confirmed", "accepted_with_notes", "needs_revision", "rejected"}:
            if not _value(row, "confirmed_by"):
                blockers.append(f"第 {index} 行缺少确认人")
            if not _value(row, "confirmed_at"):
                blockers.append(f"第 {index} 行缺少确认时间")
        blockers.extend(_scan_sensitive(row, index))

    waiting_customer_confirmation = bool(rows) and pending_count == len(rows)
    ready_for_next_retest = bool(rows) and not blockers and pending_count == 0 and rejected_count == 0
    status = (
        "ready_for_customer_confirmation_import_rehearsal"
        if ready_for_next_retest
        else "waiting_customer_confirmation"
        if waiting_customer_confirmation and not blockers
        else "blocked"
    )
    result = {
        "schema_version": SCHEMA_VERSION,
        "phase": PHASE,
        "status": status,
        "source_csv": _display_path(csv_path),
        "metrics": {
            "total_rows": len(rows),
            "pending_count": pending_count,
            "confirmed_count": confirmed_count,
            "accepted_with_notes_count": accepted_with_notes_count,
            "needs_revision_count": needs_revision_count,
            "rejected_count": rejected_count,
        },
        "readiness": {
            "ready_for_customer_confirmation_import_rehearsal": ready_for_next_retest or waiting_customer_confirmation,
            "ready_for_next_retest": ready_for_next_retest,
            "waiting_customer_confirmation": waiting_customer_confirmation,
            "formal_customer_signoff_ready": False,
        },
        "boundaries": {
            "system_prefilled_customer_confirmation": False,
            "formal_customer_signoff_performed": False,
            "raw_customer_text_exported": False,
            "real_platform_send_performed": False,
        },
        "blockers": sorted(set(blockers)),
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    _write_json(output_dir / "summary.json", result)
    _write_markdown(doc_path, result)
    return result


def main() -> int:
    result = run_h2w_pilot2_customer_confirmation_flow()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] != "blocked" else 1


if __name__ == "__main__":
    raise SystemExit(main())
