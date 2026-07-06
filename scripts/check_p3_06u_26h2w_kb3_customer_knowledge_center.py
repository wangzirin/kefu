#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PHASE = "H2W-KB3"
SCHEMA_VERSION = "p3-06u-26h2w-kb3.customer_knowledge_center.v1"
DEFAULT_OUTPUT_DIR = ROOT / "output/p3_06u_26h2w_kb3_customer_knowledge_center"
DOC_PATH = ROOT / "docs/P3-06U-26H2W_KB3_CUSTOMER_KNOWLEDGE_CENTER.md"

KB2_SUMMARY = ROOT / "output/p3_06u_26h2w_kb2_post_import_retest_and_signoff_template/summary.json"
APP_TSX = ROOT / "frontend/src/App.tsx"
KNOWLEDGE_PAGE = ROOT / "frontend/src/components/knowledge/KnowledgeWorkspacePage.tsx"
MATRIX = ROOT / "docs/FRONTEND_FUNCTION_REALITY_MATRIX.md"
TEMPLATE_CSV = ROOT / "evals/p3_06u_26h2w_kb3_customer_knowledge_center_template.csv"

REQUIRED_RECORD_TYPES = {
    "business_object",
    "standard_qa",
    "process_policy",
    "forbidden_commitment",
    "handoff_rule",
}

REQUIRED_FRONTEND_MARKERS = [
    "data-h2w-kb3-knowledge-center=\"true\"",
    "客户知识中心",
    "业务对象",
    "标准问答",
    "流程政策",
    "禁用承诺与转人工规则",
    "导入资料 → 预检 → 发布 → 复测 → 确认 → 质量报告",
    "CSV 模板可直接转换为资料包；XLSX 模板用于客户填写，试跑 v1 先另存为 CSV 后导入。PDF、DOCX 原件只作为来源留档",
]

OVERCLAIM_PHRASES = [
    "自动解析所有 PDF",
    "自动解析所有 DOCX",
    "自动解析所有 XLSX",
    "导入即启用",
    "正式客户签收已完成",
    "正式准确率签收已完成",
    "真实外发已开启",
]


def _display_path(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace") if path.exists() else ""


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _read_template_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _write_markdown(path: Path, result: dict[str, Any]) -> None:
    lines = [
        "# H2W-KB3 客户知识中心产品化门禁",
        "",
        "## 结论",
        "",
        f"- 阶段状态：`{result['status']}`",
        f"- 四层知识模板：`{str(result['readiness']['four_layer_template_ready']).lower()}`",
        f"- 前端知识中心：`{str(result['readiness']['frontend_customer_knowledge_center_ready']).lower()}`",
        "",
        "## 固定流程",
        "",
        "- 导入资料",
        "- 预检",
        "- 发布",
        "- 复测",
        "- 确认",
        "- 质量报告",
        "",
        "## 四层知识",
        "",
        "- 业务对象：产品、服务、价格、门店、课程、套餐等。",
        "- 标准问答：高频问题、标准答法、可引用来源。",
        "- 流程政策：售后、退款、发货、预约、开票、服务边界。",
        "- 禁用承诺与转人工规则：不能承诺什么，什么情况必须人工处理。",
        "",
        "## 阻断项",
        "",
    ]
    lines.extend([f"- {item}" for item in result["blockers"]] or ["- 无"])
    lines.extend(
        [
            "",
            "## 边界",
            "",
            "- CSV/XLSX 模板优先；PDF/DOCX 原件先作为来源留档和人工整理依据。",
            "- 知识评测仍是客服答案质量候选评测，不是正式线上准确率签收。",
            "- 导入知识不等于启用知识，启用前必须复测。",
            "- 真实外发继续关闭。",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_h2w_kb3_customer_knowledge_center(
    *,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    doc_path: Path = DOC_PATH,
    kb2_summary: Path = KB2_SUMMARY,
) -> dict[str, Any]:
    blockers: list[str] = []
    kb2 = _read_json(kb2_summary)
    if kb2.get("status") != "ready_for_customer_specific_knowledge_retest_template":
        blockers.append(f"KB2 上游状态不满足：{kb2.get('status') or 'missing'}")

    app_text = _read_text(APP_TSX)
    knowledge_page_text = _read_text(KNOWLEDGE_PAGE)
    frontend_text = app_text + "\n" + knowledge_page_text
    matrix_text = _read_text(MATRIX)
    template_rows = _read_template_rows(TEMPLATE_CSV)
    record_types = {row.get("record_type", "").strip() for row in template_rows}
    required_markers = {marker: marker in frontend_text for marker in REQUIRED_FRONTEND_MARKERS}
    frontend_missing = [marker for marker, present in required_markers.items() if not present]
    if frontend_missing:
        blockers.extend([f"前端知识中心缺少标记或文案：{marker}" for marker in frontend_missing])

    template_checks = {
        "template_exists": TEMPLATE_CSV.exists(),
        "template_has_required_record_types": REQUIRED_RECORD_TYPES.issubset(record_types),
        "template_rows_enough": len(template_rows) >= 5,
        "template_has_source_uri": all(row.get("source_uri") for row in template_rows),
        "template_has_expected_behavior": all(row.get("expected_behavior") for row in template_rows),
    }
    blockers.extend([f"KB3 客户知识模板不满足：{name}" for name, passed in template_checks.items() if not passed])

    overclaims = [phrase for phrase in OVERCLAIM_PHRASES if phrase in frontend_text or phrase in matrix_text]
    blockers.extend([f"知识中心存在越界文案：{phrase}" for phrase in overclaims])

    if "知识评测" not in frontend_text or "不等同完整客服事实准确率" not in frontend_text:
        blockers.append("前端没有保留知识评测不是完整客服事实准确率的边界")

    result = {
        "schema_version": SCHEMA_VERSION,
        "phase": PHASE,
        "status": "blocked" if blockers else "customer_knowledge_center_productized",
        "template": {
            "path": _display_path(TEMPLATE_CSV),
            "row_count": len(template_rows),
            "record_types": sorted(record_types),
        },
        "frontend_markers": required_markers,
        "template_checks": template_checks,
        "blockers": sorted(set(blockers)),
        "readiness": {
            "four_layer_template_ready": not blockers and template_checks["template_has_required_record_types"],
            "frontend_customer_knowledge_center_ready": not blockers and not frontend_missing,
            "customer_can_self_prepare_knowledge": not blockers,
            "automatic_pdf_docx_xlsx_parsing_ready": False,
            "formal_accuracy_signoff_ready": False,
            "real_platform_send_ready": False,
        },
        "boundaries": {
            "import_is_not_enable": True,
            "evaluation_is_not_formal_online_accuracy": True,
            "real_platform_send_performed": False,
            "customer_confirmation_faked": False,
        },
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    _write_json(output_dir / "summary.json", result)
    _write_markdown(doc_path, result)
    return result


def main() -> int:
    result = run_h2w_kb3_customer_knowledge_center()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] != "blocked" else 1


if __name__ == "__main__":
    raise SystemExit(main())
