#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PHASE = "H2W-NC3"
SCHEMA_VERSION = "p3-06u-26h2w-nc3.customer_material_precheck_productization.v1"
OUTPUT_DIR = ROOT / "output/p3_06u_26h2w_nc3_customer_material_precheck_productization"
DOC_PATH = ROOT / "docs/P3-06U-26H2W_NC3_CUSTOMER_MATERIAL_PRECHECK_PRODUCTIZATION.md"

SCHEMA_PATH = ROOT / "backend/app/schemas/pilot.py"
SERVICE_PATH = ROOT / "backend/app/services/pilot.py"
ROUTER_PATH = ROOT / "backend/app/api/pilot.py"
TEST_PATH = ROOT / "backend/tests/test_pilot_api.py"
CLIENT_PATH = ROOT / "frontend/src/api/client.ts"
APP_PATH = ROOT / "frontend/src/App.tsx"
STYLE_PATH = ROOT / "frontend/src/styles.css"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _write_doc(path: Path, result: dict[str, Any]) -> None:
    lines = [
        "# H2W-NC3 客户资料接收与预检产品化",
        "",
        "## 结论",
        "",
        f"- 阶段状态：`{result['status']}`",
        "- 范围：把客户资料预检从一次性表单升级为可追踪的资料批次流程。",
        "- 当前不保存客户原文，不打开真实外发，不标记客户签收，不生成正式安装包。",
        "",
        "## 已纳入门禁",
        "",
    ]
    for key, value in result["checks"].items():
        lines.append(f"- {key}：`{value}`")
    lines.extend(["", "## 阻断项", ""])
    lines.extend([f"- {item}" for item in result["blockers"]] or ["- 无"])
    lines.extend(
        [
            "",
            "## 产品化结果",
            "",
            "- 后端新增资料批次只读接口，返回最近预检批次、阻断数量、脱敏风险数量和 ready 边界。",
            "- 前端试点准备页支持从本地 CSV/JSON 填入资料草稿、刷新资料批次，并展示最近批次状态。",
            "- 批次列表只返回 hash、统计和状态，不返回客户问题原文、标准答案全文、密钥或平台 payload。",
            "- 预检通过只代表可以进入固定文件接收目录，不代表真实客户资料 ready。",
            "",
            "## 边界",
            "",
            "- 真实平台外发仍关闭。",
            "- 真实渠道闭环仍未完成。",
            "- 正式客户签收仍未完成。",
            "- 签名 dmg/exe 安装器仍未完成。",
            "- 内部样板或预检批次不能冒充真实客户资料。",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_nc3_gate() -> dict[str, Any]:
    schema = _read(SCHEMA_PATH)
    service = _read(SERVICE_PATH)
    router = _read(ROUTER_PATH)
    tests = _read(TEST_PATH)
    client = _read(CLIENT_PATH)
    app = _read(APP_PATH)
    styles = _read(STYLE_PATH)

    checks = {
        "schema_exposes_batch_list": "CustomerMaterialBatchListRead" in schema
        and "latest_batch" in schema
        and "raw_materials_persisted" not in schema,
        "service_exposes_hash_only_batch_list": "list_customer_material_batches" in service
        and "CUSTOMER_MATERIAL_BATCH_LIST_SCHEMA_VERSION" in service
        and "returns_material_hashes_only" in service
        and "returns_question_hashes_only" in service
        and "returns_manifest_summary_only" in service
        and "raw_materials_persisted" in service,
        "service_keeps_boundaries_closed": "real_platform_send_ready" in service
        and "formal_customer_signoff_ready" in service
        and "real_platform_send_performed" in service,
        "router_requires_knowledge_permission": '"/tenants/{tenant_id}/customer-materials/batches"' in router
        and 'require_permission("knowledge.manage")' in router,
        "tests_cover_empty_passed_blocked_and_no_raw_leak": (
            "test_customer_material_batches_list_starts_empty_then_shows_hash_only_precheck_history" in tests
            and "blocked_latest_material_precheck" in tests
            and "客户专属隐私问题不应回显" in tests
            and "not in str(body)" in tests
            and "not in str(list_body)" in tests
        ),
        "frontend_client_has_batch_contract": "CustomerMaterialBatchList" in client
        and "getCustomerMaterialBatches" in client
        and "/customer-materials/batches" in client,
        "frontend_ui_has_real_actions": "刷新资料批次" in app
        and "从本地 CSV 填入" in app
        and "从本地 JSON 填入" in app
        and "资料批次" in app
        and "批次列表只显示统计和状态" in app,
        "frontend_rejects_binary_sources_for_precheck": all(
            marker in app for marker in ["XLSX", "PDF", "DOCX", "CSV", "JSON", "file.size > 900_000"]
        ),
        "frontend_styles_present": "pilot-file-loader" in styles
        and "pilot-batch-history" in styles
        and "pilot-latest-batch.is-precheck_passed_waiting_file_drop" in styles,
        "no_customer_visible_overclaim_in_added_flow": all(
            phrase not in app
            for phrase in [
                "真实客户资料已完成",
                "正式客户签收完成",
                "真实外发已接通",
                "全渠道已上线",
            ]
        ),
    }

    blockers = [f"{name} 未通过" for name, passed in checks.items() if not passed]
    status = "customer_material_precheck_productization_ready" if not blockers else "blocked"
    result = {
        "schema_version": SCHEMA_VERSION,
        "phase": PHASE,
        "status": status,
        "blockers": sorted(blockers),
        "checks": checks,
        "readiness": {
            "customer_material_precheck_productization_ready": not blockers,
            "batch_history_api_ready": checks["router_requires_knowledge_permission"],
            "frontend_batch_history_ready": checks["frontend_ui_has_real_actions"],
            "raw_materials_persisted": False,
            "real_customer_materials_ready": False,
            "real_platform_send_ready": False,
            "formal_customer_signoff_ready": False,
            "signed_dmg_exe_ready": False,
        },
        "boundaries": {
            "real_platform_send_ready": False,
            "real_channel_closed_loop_ready": False,
            "formal_customer_signoff_ready": False,
            "signed_dmg_exe_ready": False,
            "raw_customer_materials_persisted": False,
        },
        "not_ready_for": [
            "真实平台外发",
            "真实渠道闭环",
            "正式客户验收签收",
            "签名 dmg/exe 安装器",
            "把预检批次当成真实客户资料 ready",
        ],
        "evidence_paths": [
            str(SCHEMA_PATH.relative_to(ROOT)),
            str(SERVICE_PATH.relative_to(ROOT)),
            str(ROUTER_PATH.relative_to(ROOT)),
            str(TEST_PATH.relative_to(ROOT)),
            str(CLIENT_PATH.relative_to(ROOT)),
            str(APP_PATH.relative_to(ROOT)),
            str(STYLE_PATH.relative_to(ROOT)),
            str(DOC_PATH.relative_to(ROOT)),
            str((OUTPUT_DIR / "summary.json").relative_to(ROOT)),
        ],
    }
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    _write_json(OUTPUT_DIR / "summary.json", result)
    _write_doc(DOC_PATH, result)
    return result


def main() -> int:
    result = run_nc3_gate()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] != "blocked" else 1


if __name__ == "__main__":
    raise SystemExit(main())
