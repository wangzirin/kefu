#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PHASE = "H2W-NC4"
SCHEMA_VERSION = "p3-06u-26h2w-nc4.knowledge_memory_mesh_overview.v1"
OUTPUT_DIR = ROOT / "output/p3_06u_26h2w_nc4_knowledge_memory_mesh_overview"
DOC_PATH = ROOT / "docs/P3-06U-26H2W_NC4_KNOWLEDGE_MEMORY_MESH_OVERVIEW.md"

SCHEMA_PATH = ROOT / "backend/app/schemas/knowledge.py"
SERVICE_PATH = ROOT / "backend/app/services/knowledge.py"
ROUTER_PATH = ROOT / "backend/app/api/knowledge.py"
TEST_PATH = ROOT / "backend/tests/test_knowledge_api.py"
CLIENT_PATH = ROOT / "frontend/src/api/client.ts"
APP_PATH = ROOT / "frontend/src/App.tsx"
COMPONENT_PATH = ROOT / "frontend/src/components/knowledge/KnowledgeWorkspacePage.tsx"
STYLE_PATH = ROOT / "frontend/src/styles.css"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _write_doc(path: Path, result: dict[str, Any]) -> None:
    lines = [
        "# H2W-NC4 知识中心 v2 与 Memory Mesh 化",
        "",
        "## 结论",
        "",
        f"- 阶段状态：`{result['status']}`",
        "- 范围：新增知识网络总览，把资料批次、知识卡片、业务对象、问题样本、质量标签与错因纳入同一张只读证据链。",
        "- 当前能力是本地知识证据链和质量闭环总览，不代表真实平台已自动回复，也不代表完整 Memory Mesh 已全部完成。",
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
            "- 后端新增 `GET /api/tenants/{tenant_id}/knowledge-memory-mesh-overview`，权限沿用 `knowledge.read`。",
            "- 响应只返回计数、状态、hash/source_uri 覆盖和边界，不返回客户原文、文档正文或草稿全文。",
            "- 前端知识运营、知识缺口、知识评测三个入口统一展示“知识网络总览”。",
            "- 总览包含五类节点和八段回复证据链：入站样本、检索结果、引用 chunk、模型调用、最终草稿、转人工理由、质量标签、修复后的知识版本。",
            "- `full_memory_mesh_ready`、`real_platform_send_ready` 和 `formal_customer_signoff_ready` 均保持真实边界，不做越界承诺。",
            "",
            "## 边界",
            "",
            "- 真实平台外发仍关闭。",
            "- 真实渠道闭环仍未完成。",
            "- 正式客户签收仍未完成。",
            "- 签名 dmg/exe 安装器仍未完成。",
            "- 当前是 Memory Mesh 读模型与证据链总览，不是完整图数据库或生产级自动修复系统。",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_nc4_gate() -> dict[str, Any]:
    schema = _read(SCHEMA_PATH)
    service = _read(SERVICE_PATH)
    router = _read(ROUTER_PATH)
    tests = _read(TEST_PATH)
    client = _read(CLIENT_PATH)
    app = _read(APP_PATH)
    component = _read(COMPONENT_PATH)
    styles = _read(STYLE_PATH)

    required_nodes = ["资料批次", "知识卡片", "业务对象", "真实/样本问题", "质量标签与错因"]
    required_steps = ["入站样本", "检索结果", "引用 chunk", "模型调用", "最终草稿", "转人工理由", "质量标签", "修复后的知识版本"]
    forbidden_response_fields = ["raw_text_included\": True", "draft_reply_included\": True", "real_platform_send_ready\": True"]

    checks = {
        "schema_exposes_memory_mesh_contract": "KnowledgeMemoryMeshOverviewRead" in schema
        and "KnowledgeMeshNodeRead" in schema
        and "KnowledgeMeshProvenanceStepRead" in schema
        and "source_authority" in schema
        and "quality_loop" in schema
        and "readiness" in schema
        and "boundaries" in schema,
        "service_builds_five_nodes": "get_knowledge_memory_mesh_overview" in service
        and all(node in service for node in required_nodes),
        "service_builds_provenance_steps": all(step in service for step in required_steps)
        and "source_uri、content_hash、document_chunk_id" in service,
        "service_keeps_sensitive_payloads_out": "raw_text_included" in service
        and "draft_reply_included" in service
        and not any(marker in service for marker in forbidden_response_fields),
        "service_keeps_external_boundaries_false": '"real_platform_send_ready": False' in service
        and '"formal_customer_signoff_ready": False' in service
        and '"full_memory_mesh_ready"' in service,
        "router_requires_knowledge_read": '"/tenants/{tenant_id}/knowledge-memory-mesh-overview"' in router
        and "KnowledgeMemoryMeshOverviewRead" in router
        and "require_permission(KNOWLEDGE_READ_PERMISSION)" in router,
        "tests_cover_api_and_no_raw_text": (
            "test_owner_can_read_knowledge_memory_mesh_overview_without_raw_text" in tests
            and "raw_text not in json.dumps" in tests
            and "real_platform_send_ready" in tests
        ),
        "frontend_client_has_api": "KnowledgeMemoryMeshOverview" in client
        and "getKnowledgeMemoryMeshOverview" in client
        and "/knowledge-memory-mesh-overview" in client,
        "frontend_state_refreshes_overview": "KnowledgeMemoryMeshState" in app
        and "refreshKnowledgeMemoryMeshOverview" in app
        and "getKnowledgeMemoryMeshOverview" in app,
        "frontend_renders_mesh_card": "知识网络总览" in component
        and all(node in component for node in ["资料批次", "引用链路", "答案质量", "真实外发"])
        and "当前只展示本地知识证据链" not in component,
        "frontend_styles_present": "knowledge-memory-mesh" in styles
        and "knowledge-memory-node-grid" in styles
        and "knowledge-memory-chain" in styles,
        "no_customer_visible_engineering_terms_in_mesh": all(
            term not in component
            for term in ["H2W", "P3", "dry-run", "provider", "outbox", "sandbox", "rehearsal"]
        ),
    }

    blockers = [f"{name} 未通过" for name, passed in checks.items() if not passed]
    status = "knowledge_memory_mesh_overview_ready" if not blockers else "blocked"
    result = {
        "schema_version": SCHEMA_VERSION,
        "phase": PHASE,
        "status": status,
        "blockers": sorted(blockers),
        "checks": checks,
        "readiness": {
            "knowledge_memory_mesh_overview_ready": not blockers,
            "full_memory_mesh_ready": False,
            "real_platform_send_ready": False,
            "formal_customer_signoff_ready": False,
            "signed_dmg_exe_ready": False,
        },
        "boundaries": {
            "raw_text_included": False,
            "draft_reply_included": False,
            "real_platform_send_ready": False,
            "formal_customer_signoff_ready": False,
            "complete_graph_database_ready": False,
        },
        "not_ready_for": [
            "真实平台外发",
            "真实渠道闭环",
            "正式客户验收签收",
            "签名 dmg/exe 安装器",
            "完整图数据库式 Memory Mesh",
        ],
        "evidence_paths": [
            str(SCHEMA_PATH.relative_to(ROOT)),
            str(SERVICE_PATH.relative_to(ROOT)),
            str(ROUTER_PATH.relative_to(ROOT)),
            str(TEST_PATH.relative_to(ROOT)),
            str(CLIENT_PATH.relative_to(ROOT)),
            str(APP_PATH.relative_to(ROOT)),
            str(COMPONENT_PATH.relative_to(ROOT)),
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
    result = run_nc4_gate()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] != "blocked" else 1


if __name__ == "__main__":
    raise SystemExit(main())
