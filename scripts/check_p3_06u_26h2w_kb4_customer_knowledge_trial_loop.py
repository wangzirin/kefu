#!/usr/bin/env python3
from __future__ import annotations

import csv
import html
import json
import zipfile
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PHASE = "H2W-KB4"
SCHEMA_VERSION = "p3-06u-26h2w-kb4.customer_knowledge_trial_loop.v1"
DEFAULT_OUTPUT_DIR = ROOT / "output/p3_06u_26h2w_kb4_customer_knowledge_trial_loop"
DOC_PATH = ROOT / "docs/P3-06U-26H2W_KB4_CUSTOMER_KNOWLEDGE_TRIAL_LOOP.md"

KB3_SUMMARY = ROOT / "output/p3_06u_26h2w_kb3_customer_knowledge_center/summary.json"
APP_TSX = ROOT / "frontend/src/App.tsx"
KNOWLEDGE_PAGE = ROOT / "frontend/src/components/knowledge/KnowledgeWorkspacePage.tsx"
CSV_TEMPLATE = ROOT / "evals/p3_06u_26h2w_kb3_customer_knowledge_center_template.csv"

REQUIRED_RECORD_TYPES = {
    "business_object",
    "standard_qa",
    "process_policy",
    "forbidden_commitment",
    "handoff_rule",
}
REQUIRED_FLOW_TERMS = ["导入资料", "预检", "发布", "复测", "确认", "质量报告"]
REQUIRED_FRONTEND_TERMS = [
    "客户知识中心",
    "业务对象",
    "标准问答",
    "流程政策",
    "禁用承诺与转人工规则",
    "CSV 模板可直接转换为资料包",
    "XLSX 模板用于客户填写",
    "PDF、DOCX 原件只作为来源留档",
    "不等同完整客服事实准确率",
]
OVERCLAIMS = [
    "自动解析所有 PDF",
    "自动解析所有 DOCX",
    "自动解析所有 XLSX",
    "导入即启用",
    "正式线上准确率签收已完成",
    "正式客户验收已完成",
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


def _read_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _column_name(index: int) -> str:
    name = ""
    while index:
        index, rem = divmod(index - 1, 26)
        name = chr(65 + rem) + name
    return name


def _write_minimal_xlsx(path: Path, rows: list[dict[str, str]]) -> None:
    headers = list(rows[0].keys()) if rows else []
    table_rows = [headers] + [[row.get(header, "") for header in headers] for row in rows]
    sheet_cells: list[str] = []
    for row_index, row in enumerate(table_rows, start=1):
        cells = []
        for col_index, value in enumerate(row, start=1):
            ref = f"{_column_name(col_index)}{row_index}"
            cells.append(f'<c r="{ref}" t="inlineStr"><is><t>{html.escape(str(value))}</t></is></c>')
        sheet_cells.append(f'<row r="{row_index}">{"".join(cells)}</row>')
    sheet_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
        f'<sheetData>{"".join(sheet_cells)}</sheetData></worksheet>'
    )
    workbook_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
        'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
        '<sheets><sheet name="客户知识资料" sheetId="1" r:id="rId1"/></sheets></workbook>'
    )
    rels_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>'
        "</Relationships>"
    )
    workbook_rels_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/>'
        "</Relationships>"
    )
    content_types_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
        '<Default Extension="xml" ContentType="application/xml"/>'
        '<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
        '<Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
        "</Types>"
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml", content_types_xml)
        archive.writestr("_rels/.rels", rels_xml)
        archive.writestr("xl/workbook.xml", workbook_xml)
        archive.writestr("xl/_rels/workbook.xml.rels", workbook_rels_xml)
        archive.writestr("xl/worksheets/sheet1.xml", sheet_xml)


def _write_markdown(path: Path, result: dict[str, Any]) -> None:
    lines = [
        "# H2W-KB4 客户知识资料试跑闭环",
        "",
        "## 结论",
        "",
        f"- 阶段状态：`{result['status']}`",
        f"- CSV 模板：`{result['templates']['csv_template']}`",
        f"- XLSX 模板：`{result['templates']['xlsx_template']}`",
        "",
        "## 固定 6 步",
        "",
        "- 导入资料",
        "- 预检",
        "- 发布",
        "- 复测",
        "- 确认",
        "- 质量报告",
        "",
        "## 边界",
        "",
        "- CSV 可直接导入，XLSX 是同列名填写模板；本地试跑 v1 先另存为 CSV 后导入。",
        "- PDF/DOCX 只作为来源资料，不承诺全自动高质量入库。",
        "- 知识评测是客服答案质量候选评测，不是正式线上准确率签收。",
        "- 真实外发继续关闭。",
        "",
        "## 阻断项",
        "",
    ]
    lines.extend([f"- {item}" for item in result["blockers"]] or ["- 无"])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_h2w_kb4_customer_knowledge_trial_loop(
    *,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    doc_path: Path = DOC_PATH,
) -> dict[str, Any]:
    blockers: list[str] = []
    kb3 = _read_json(KB3_SUMMARY)
    if kb3.get("status") != "customer_knowledge_center_productized":
        blockers.append(f"KB3 上游状态不满足：{kb3.get('status') or 'missing'}")

    frontend_text = "\n".join([_read_text(APP_TSX), _read_text(KNOWLEDGE_PAGE)])
    missing_terms = [term for term in REQUIRED_FRONTEND_TERMS if term not in frontend_text]
    blockers.extend([f"知识中心前端缺少客户可理解口径：{term}" for term in missing_terms])
    flow_missing = [term for term in REQUIRED_FLOW_TERMS if term not in frontend_text]
    blockers.extend([f"知识中心 6 步流程缺少：{term}" for term in flow_missing])
    blockers.extend([f"知识中心存在越界文案：{term}" for term in OVERCLAIMS if term in frontend_text])

    rows = _read_csv_rows(CSV_TEMPLATE)
    record_types = {row.get("record_type", "").strip() for row in rows}
    template_checks = {
        "csv_template_exists": CSV_TEMPLATE.exists(),
        "csv_template_has_rows": len(rows) >= 5,
        "csv_template_has_required_record_types": REQUIRED_RECORD_TYPES.issubset(record_types),
        "csv_template_has_source_uri": bool(rows) and all(row.get("source_uri") for row in rows),
        "csv_template_has_expected_behavior": bool(rows) and all(row.get("expected_behavior") for row in rows),
    }
    blockers.extend([f"知识模板不满足：{name}" for name, passed in template_checks.items() if not passed])

    output_dir.mkdir(parents=True, exist_ok=True)
    xlsx_template = output_dir / "wanfa_customer_knowledge_trial_template.xlsx"
    if rows:
        _write_minimal_xlsx(xlsx_template, rows)
    if not xlsx_template.exists():
        blockers.append("XLSX 知识资料模板未生成")

    result = {
        "schema_version": SCHEMA_VERSION,
        "phase": PHASE,
        "status": "blocked" if blockers else "customer_knowledge_trial_loop_ready",
        "templates": {
            "csv_template": _display_path(CSV_TEMPLATE),
            "xlsx_template": _display_path(xlsx_template),
            "xlsx_template_exists": xlsx_template.exists(),
            "record_types": sorted(record_types),
            "row_count": len(rows),
        },
        "flow": REQUIRED_FLOW_TERMS,
        "template_checks": template_checks,
        "blockers": sorted(set(blockers)),
        "readiness": {
            "customer_can_import_csv_template": not blockers,
            "customer_can_prepare_xlsx_template": xlsx_template.exists(),
            "pdf_docx_auto_parse_ready": False,
            "formal_online_accuracy_signoff_ready": False,
            "real_platform_send_ready": False,
        },
        "boundaries": {
            "csv_xlsx_template_are_trial_inputs": True,
            "pdf_docx_are_source_material_only": True,
            "evaluation_is_candidate_quality_not_formal_accuracy": True,
            "real_platform_send_performed": False,
            "customer_confirmation_faked": False,
        },
    }
    _write_json(output_dir / "summary.json", result)
    _write_markdown(doc_path, result)
    return result


def main() -> int:
    result = run_h2w_kb4_customer_knowledge_trial_loop()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] != "blocked" else 1


if __name__ == "__main__":
    raise SystemExit(main())
