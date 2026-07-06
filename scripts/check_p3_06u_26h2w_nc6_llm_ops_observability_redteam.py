#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PHASE = "H2W-NC6"
OUTPUT_DIR = ROOT / "output/p3_06u_26h2w_nc6_llm_ops_observability_redteam"
DOC_PATH = ROOT / "docs/P3-06U-26H2W_NC6_LLM_OPS_OBSERVABILITY_REDTEAM.md"

FILES = {
    "schema": ROOT / "backend/app/schemas/llm_ops.py",
    "service": ROOT / "backend/app/services/llm_ops.py",
    "api": ROOT / "backend/app/api/knowledge.py",
    "backend_test": ROOT / "backend/tests/test_llm_ops_readiness_api.py",
    "frontend_client": ROOT / "frontend/src/api/client.ts",
    "frontend_app": ROOT / "frontend/src/App.tsx",
}

SUMMARY_FILES = {
    "nc5": ROOT / "output/p3_06u_26h2w_nc5_production_retrieval_governance/summary.json",
    "model1": ROOT / "output/p3_06u_26h2w_model1_bailian_cost_sample/summary.json",
    "trial1": ROOT / "output/p3_06u_26h2w_trial1_internal_100q_rehearsal_report/summary.json",
}


def _display_path(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _write_markdown(path: Path, result: dict[str, Any]) -> None:
    lines = [
        "# H2W-NC6 模型观测、成本与红队治理",
        "",
        "## 结论",
        "",
        f"- 阶段状态：`{result['status']}`",
        f"- 后端接口 ready：`{str(result['readiness']['backend_api_ready']).lower()}`",
        f"- 前端展示 ready：`{str(result['readiness']['frontend_ready']).lower()}`",
        f"- 成本台账 ready：`{str(result['readiness']['cost_ledger_ready']).lower()}`",
        f"- 链路追踪 ready：`{str(result['readiness']['trace_coverage_ready']).lower()}`",
        f"- 红队闭环 ready：`{str(result['readiness']['redteam_ready']).lower()}`",
        "",
        "## 当前阻断项",
        "",
    ]
    lines.extend([f"- {item}" for item in result["blockers"]] or ["- 无"])
    lines.extend(
        [
            "",
            "## 已纳入的证据",
            "",
        ]
    )
    for key, item in result["evidence"].items():
        lines.append(f"- {key}: `{item['path']}`，存在：`{str(item['present']).lower()}`")
    lines.extend(
        [
            "",
            "## 固定边界",
            "",
            "- 本阶段新增的是模型运营可观测与红队治理入口，不代表真实平台自动回复已开启。",
            "- 没有 5-10 条真实模型小样本、价格版本和延迟记录时，不能写客户侧真实模型成本报告。",
            "- 没有提示注入、隐私泄露、禁用承诺和越权操作题集的人工标签时，不能写红队安全闭环完成。",
            "- 显式指定模型服务商失败不得静默切换；只有自动路由允许按策略降级。",
            "- 真实外发、真实渠道、客户签收、生产 SLA 和签名安装包仍未完成。",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_nc6_gate(*, output_dir: Path = OUTPUT_DIR) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    blockers: list[str] = []
    required_markers = {
        "schema": [
            "class LlmOpsReadinessSummary",
            "LlmOpsCostLedger",
            "LlmOpsRedteamReadiness",
            "explicit_provider_no_silent_fallback",
        ],
        "service": [
            "SCHEMA_VERSION",
            "get_llm_ops_readiness_summary",
            "ModelCallRecord",
            "ReplyCitationSnapshot",
            "KnowledgeEvaluationCase",
            "raw_text_logged_count",
            "redteam_case_count",
            "explicit_provider_no_silent_fallback",
        ],
        "api": ["llm-ops-readiness", "LlmOpsReadinessSummary", "get_llm_ops_readiness_summary"],
        "backend_test": [
            "test_owner_can_read_llm_ops_readiness_without_external_calls",
            "test_llm_ops_readiness_blocks_raw_text_logged_model_records",
            "test_agent_cannot_read_llm_ops_readiness",
        ],
        "frontend_client": ["LlmOpsReadinessSummary", "getLlmOpsReadinessSummary"],
        "frontend_app": ["模型观测与红队", "llmOpsReadiness", "原文落库", "安全题集"],
    }

    marker_ready: dict[str, bool] = {}
    for key, markers in required_markers.items():
        path = FILES[key]
        text = _read(path)
        ready = path.exists() and all(marker in text for marker in markers)
        marker_ready[key] = ready
        if not ready:
            blockers.append(f"{_display_path(path)} 缺少 NC6 必需标记")

    nc5 = _read_json(SUMMARY_FILES["nc5"])
    model1 = _read_json(SUMMARY_FILES["model1"])
    trial1 = _read_json(SUMMARY_FILES["trial1"])
    nc5_ready = str(nc5.get("status", "")).startswith("production_retrieval_governance_ready")
    cost_ledger_ready = model1.get("status") == "passed_real_small_sample_cost_rehearsal"
    trace_coverage_ready = bool(trial1.get("status"))
    redteam_ready = False

    if not nc5_ready:
        blockers.append("NC5 生产检索治理摘要未 ready，NC6 只能作为独立接口候选。")
    if not cost_ledger_ready:
        blockers.append("缺少 5-10 条真实模型小样本成本证据，模型成本报告只能保持候选。")
    if not trace_coverage_ready:
        blockers.append("缺少内部题库试跑证据，无法判断回复链路追踪覆盖。")
    blockers.append("红队题集和人工标签尚未形成完整闭环，不能写成安全评测完成。")

    backend_api_ready = all(marker_ready[key] for key in ("schema", "service", "api", "backend_test"))
    frontend_ready = marker_ready["frontend_client"] and marker_ready["frontend_app"]
    status = (
        "llm_ops_redteam_ready_for_controlled_pilot"
        if backend_api_ready and frontend_ready and cost_ledger_ready and trace_coverage_ready and redteam_ready
        else "llm_ops_observability_ready_not_redteam_complete"
        if backend_api_ready and frontend_ready
        else "blocked"
    )
    result = {
        "phase": PHASE,
        "status": status,
        "readiness": {
            "backend_api_ready": backend_api_ready,
            "frontend_ready": frontend_ready,
            "cost_ledger_ready": cost_ledger_ready,
            "trace_coverage_ready": trace_coverage_ready,
            "redteam_ready": redteam_ready,
            "real_platform_send_ready": False,
        },
        "blockers": blockers,
        "boundaries": {
            "real_platform_send_enabled": False,
            "real_channel_integrations_enabled": False,
            "formal_customer_signoff": False,
            "signed_installer_ready": False,
            "internal_rehearsal_only": True,
        },
        "evidence": {
            key: {"path": _display_path(path), "present": path.exists()}
            for key, path in {**FILES, **SUMMARY_FILES}.items()
        },
        "not_ready_for": [
            "真实平台自动外发",
            "客户正式准确率签收",
            "成熟商用全渠道客服发布",
            "生产 SLA",
        ],
    }
    _write_json(output_dir / "summary.json", result)
    _write_markdown(DOC_PATH, result)
    return result


if __name__ == "__main__":
    summary = run_nc6_gate()
    print(json.dumps(summary, ensure_ascii=False, indent=2))
