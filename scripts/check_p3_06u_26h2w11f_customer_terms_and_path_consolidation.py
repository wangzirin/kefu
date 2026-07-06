#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_DIR = ROOT / "output/p3_06u_26h2w11f_customer_terms_and_path_consolidation"
APP_PATH = ROOT / "frontend/src/App.tsx"
MATRIX_PATH = ROOT / "docs/FRONTEND_FUNCTION_REALITY_MATRIX.md"
DOC_PATH = ROOT / "docs/P3-06U-26H2W11F_CUSTOMER_TERMS_AND_PATH_CONSOLIDATION.md"
H2W11D_GATE_PATH = ROOT / "scripts/check_p3_06u_26h2w11d_customer_knowledge_publish_path.py"
H2W11E_MJS_PATH = ROOT / "scripts/check_p3_06u_26h2w11e_owner_customer_knowledge_trial.mjs"
H2W11E_STATIC_PATH = ROOT / "scripts/check_p3_06u_26h2w11e_owner_customer_knowledge_trial.py"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _require_contains(name: str, content: str, needles: list[str]) -> list[str]:
    return [f"{name} missing {needle!r}" for needle in needles if needle not in content]


def _extract_section(content: str, marker: str) -> str:
    start = content.find(marker)
    if start < 0:
        return ""
    end = content.find("</section>", start)
    return content[start:] if end < 0 else content[start : end + len("</section>")]


def run_h2w11f_customer_terms_and_path_consolidation_gate(
    *,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
) -> dict[str, Any]:
    blockers: list[str] = []
    warnings: list[str] = []

    required_files = [
        APP_PATH,
        MATRIX_PATH,
        DOC_PATH,
        H2W11D_GATE_PATH,
        H2W11E_MJS_PATH,
        H2W11E_STATIC_PATH,
    ]
    for path in required_files:
        if not path.exists():
            blockers.append(f"required file missing: {path.relative_to(ROOT)}")

    if blockers:
        result = {
            "phase": "H2W-11F",
            "status": "blocked",
            "blockers": blockers,
            "warnings": warnings,
            "boundaries": _boundaries(),
        }
        _write_summary(output_dir, result)
        return result

    app = _read(APP_PATH)
    matrix = _read(MATRIX_PATH)
    doc = _read(DOC_PATH)
    h2w11d_gate = _read(H2W11D_GATE_PATH)
    h2w11e_mjs = _read(H2W11E_MJS_PATH)
    h2w11e_static = _read(H2W11E_STATIC_PATH)

    publish_section = _extract_section(app, 'data-h2w11d-customer-publish-path="true"')
    intake_section = _extract_section(app, 'data-h2w3c-customer-intake="true"')
    update_package_section = _extract_section(app, 'data-knowledge-update-package="p3-06u-26h2d"')

    blockers.extend(
        _require_contains(
            "frontend/src/App.tsx",
            app,
            [
                'data-h2w11d-customer-publish-path="true"',
                'data-h2w11d-action="convert-customer-intake"',
                'data-h2w11d-action="preview-update-package"',
                'data-h2w11d-action="import-update-package"',
                "applyCustomerKnowledgeIntakePackage",
                "onPreviewUpdatePackage",
                "onImportUpdatePackage",
                "onCheckPublishDocument(firstReadyDocument)",
                "onPublishDocument(firstReadyDocument)",
                "知识维护总流程",
                "导入资料 → 预检 → 发布 → 复测 → 确认 → 质量报告",
                "生成资料包",
                "检查资料包",
                "导入知识库",
                "启用前复测",
                "启用知识",
                "查看复测题库",
                "客户资料整理",
                "知识资料包导入",
                "本地确认记录不是正式验收",
                "真实外发继续关闭",
            ],
        )
    )

    legacy_terms_by_section = {
        "customer publish path": [
            "客户知识发布闭环",
            "导入 → 预检 → 发布 → 回归评测 → 报告 → 签收",
            "转换客户资料",
            "预检更新包",
            "发布前试跑",
            "确认发布",
            "进入知识评测",
            "本地签收记录不是正式电子签章",
        ],
        "customer intake": [
            "客户资料导入助手",
            "转换为更新包",
            "预检差异",
            "知识更新包预检",
        ],
        "knowledge package": [
            "知识更新包导入",
            "预检差异",
            "导入更新包",
            "更新包 JSON",
        ],
    }
    section_contents = {
        "customer publish path": publish_section,
        "customer intake": intake_section,
        "knowledge package": update_package_section,
    }
    legacy_found: dict[str, list[str]] = {}
    for section_name, terms in legacy_terms_by_section.items():
        found = [term for term in terms if term in section_contents[section_name]]
        if found:
            legacy_found[section_name] = found
            blockers.append(f"{section_name} still exposes legacy/internal customer terms: {found}")

    blockers.extend(
        _require_contains(
            "scripts/check_p3_06u_26h2w11d_customer_knowledge_publish_path.py",
            h2w11d_gate,
            [
                "导入资料 → 预检 → 发布 → 复测 → 确认 → 质量报告",
                "知识维护总流程",
                "生成资料包",
                "检查资料包",
                "导入知识库",
                "启用前复测",
                "客户确认记录不是正式验收",
                "legacy/internal terms",
            ],
        )
    )
    blockers.extend(
        _require_contains(
            "scripts/check_p3_06u_26h2w11e_owner_customer_knowledge_trial.mjs",
            h2w11e_mjs,
            [
                "知识维护总流程",
                "导入资料 → 预检 → 发布 → 复测 → 确认 → 质量报告",
                "已生成知识资料包",
                "已导入知识资料包",
                "legacyTerms",
                "customer_publish_path_clicked_through_ui",
            ],
        )
    )
    blockers.extend(
        _require_contains(
            "scripts/check_p3_06u_26h2w11e_owner_customer_knowledge_trial.py",
            h2w11e_static,
            [
                "客户确认记录不是正式验收",
                "生成资料包",
                "检查资料包",
                "导入知识库",
                "知识维护总流程",
            ],
        )
    )
    blockers.extend(
        _require_contains(
            "docs/FRONTEND_FUNCTION_REALITY_MATRIX.md",
            matrix,
            [
                "H2W-11F",
                "客户资料整理",
                "知识资料包",
                "知识维护总流程",
                "生成资料包",
                "检查资料包",
                "导入知识库",
                "本地确认不是正式验收",
            ],
        )
    )
    blockers.extend(
        _require_contains(
            "docs/P3-06U-26H2W11F_CUSTOMER_TERMS_AND_PATH_CONSOLIDATION.md",
            doc,
            [
                "# H2W-11F 前端客户术语与知识维护路径收束",
                "客户资料整理",
                "知识资料包导入",
                "知识维护总流程",
                "生成资料包 -> 检查资料包 -> 导入知识库",
                "不新增真实外发",
                "不新增空按钮",
                "停止门禁",
            ],
        )
    )

    overclaims = [
        "真实外发已开启",
        "已接通全渠道",
        "正式电子签章已完成",
        "合同签收已完成",
        "完整线上准确率已完成",
    ]
    visible_text = "\n".join([publish_section, intake_section, update_package_section])
    overclaims_found = [term for term in overclaims if term in visible_text]
    if overclaims_found:
        blockers.append(f"customer knowledge sections contain overclaiming copy: {overclaims_found}")

    if "真实外发继续关闭" not in visible_text:
        blockers.append("customer knowledge sections should keep external-send-disabled boundary visible")

    result = {
        "phase": "H2W-11F",
        "status": "passed" if not blockers else "blocked",
        "blockers": blockers,
        "warnings": warnings,
        "checks": {
            "new_customer_terms_present": all(
                term in app
                for term in [
                    "知识维护总流程",
                    "客户资料整理",
                    "知识资料包导入",
                    "生成资料包",
                    "检查资料包",
                    "导入知识库",
                ]
            ),
            "legacy_terms_absent_from_customer_sections": not legacy_found,
            "h2w11e_browser_gate_updated": "legacyTerms" in h2w11e_mjs and "已生成知识资料包" in h2w11e_mjs,
            "reality_matrix_updated": "H2W-11F" in matrix and "知识维护总流程" in matrix,
            "docs_updated": "H2W-11F 前端客户术语" in doc,
        },
        "legacy_found": legacy_found,
        "boundaries": _boundaries(),
    }
    _write_summary(output_dir, result)
    return result


def _boundaries() -> dict[str, bool]:
    return {
        "provider_call_performed": False,
        "external_platform_write_performed": False,
        "real_platform_send_performed": False,
        "formal_customer_signoff_performed": False,
        "electronic_signature_performed": False,
        "real_customer_data_used": False,
        "new_backend_capability_added": False,
    }


def _write_summary(output_dir: Path, result: dict[str, Any]) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "summary.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> None:
    result = run_h2w11f_customer_terms_and_path_consolidation_gate()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if result["blockers"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
