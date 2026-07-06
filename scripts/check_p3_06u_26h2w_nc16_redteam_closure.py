#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PHASE = "H2W-NC16"
OUTPUT_DIR = ROOT / "output/p3_06u_26h2w_nc16_redteam_closure"
DOC_PATH = ROOT / "docs/P3-06U-26H2W_NC16_REDTEAM_CLOSURE.md"

FILES = {
    "schema": ROOT / "backend/app/schemas/llm_ops.py",
    "service": ROOT / "backend/app/services/llm_ops.py",
    "api_test": ROOT / "backend/tests/test_llm_ops_readiness_api.py",
    "nc6_summary": ROOT / "output/p3_06u_26h2w_nc6_llm_ops_observability_redteam/summary.json",
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
        "# H2W-NC16 红队闭环门禁",
        "",
        "## 结论",
        "",
        f"- 阶段状态：`{result['status']}`",
        f"- 五类风险覆盖规则：`{str(result['readiness']['category_gate_ready']).lower()}`",
        f"- 全部活跃红队题人工标签规则：`{str(result['readiness']['label_gate_ready']).lower()}`",
        f"- 失败样本回流规则：`{str(result['readiness']['failure_review_gate_ready']).lower()}`",
        "",
        "## 当前阻断项",
        "",
    ]
    lines.extend([f"- {item}" for item in result["blockers"]] or ["- 无"])
    lines.extend(
        [
            "",
            "## 规则说明",
            "",
            "- 红队题集至少覆盖提示注入、越狱、隐私泄露、禁用承诺和越权操作五类风险。",
            "- 只有全部活跃红队题都有最终答案人工标签，才允许进入受控试点候选。",
            "- 红队失败样本必须逐条进入知识缺口或质量复盘，不能只用任意一个知识缺口冒充闭环。",
            "- 接口仍不返回红队问题原文，避免把攻击提示、隐私样例或平台敏感信息暴露给前端。",
            "",
            "## 固定边界",
            "",
            "- 本阶段完成的是红队闭环判定规则和内部测试，不等于客户真实安全签收。",
            "- 没有真实客户题库和真实模型输出标签时，不能写成正式红队报告完成。",
            "- 真实外发、真实渠道、生产 SLA、签名安装包和客户正式签收仍未完成。",
            "",
            "## 证据文件",
            "",
        ]
    )
    for key, item in result["evidence"].items():
        lines.append(f"- {key}: `{item['path']}`，存在：`{str(item['present']).lower()}`")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_nc16_redteam_closure_gate(*, output_dir: Path = OUTPUT_DIR) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    blockers: list[str] = []
    required_markers = {
        "schema": [
            "required_minimum_cases",
            "missing_categories",
            "all_active_cases_labeled",
            "unresolved_redteam_failures",
        ],
        "service": [
            "REQUIRED_REDTEAM_CATEGORIES",
            "REQUIRED_REDTEAM_MINIMUM_CASES",
            "_redteam_run_case_failed",
            "_quality_review_items_for_run_cases",
            "category_coverage_ready",
            "all_active_cases_labeled",
            "unresolved_redteam_failures",
        ],
        "api_test": [
            "test_llm_ops_readiness_marks_redteam_ready_only_after_full_category_labels",
            "test_llm_ops_redteam_failure_requires_linked_quality_review_item",
            "redteam_evaluation_run_case",
            "unresolved_redteam_failures",
        ],
    }
    marker_ready: dict[str, bool] = {}
    for key, markers in required_markers.items():
        text = _read(FILES[key])
        ready = FILES[key].exists() and all(marker in text for marker in markers)
        marker_ready[key] = ready
        if not ready:
            blockers.append(f"{_display_path(FILES[key])} 缺少 NC16 红队闭环标记")

    nc6 = _read_json(FILES["nc6_summary"])
    nc6_present = bool(nc6)
    if not nc6_present:
        blockers.append("缺少 NC6 模型观测 summary，NC16 不能作为上游闭环补强证据。")

    code_ready = all(marker_ready.values()) and nc6_present
    status = "redteam_closure_gate_ready_internal_fixtures_only" if code_ready else "blocked"
    result = {
        "phase": PHASE,
        "status": status,
        "readiness": {
            "category_gate_ready": marker_ready.get("schema", False) and marker_ready.get("service", False),
            "label_gate_ready": marker_ready.get("service", False) and marker_ready.get("api_test", False),
            "failure_review_gate_ready": marker_ready.get("service", False) and marker_ready.get("api_test", False),
            "real_customer_redteam_run_ready": False,
            "formal_security_signoff_ready": False,
        },
        "blockers": blockers,
        "boundaries": {
            "real_platform_send_enabled": False,
            "real_channel_integrations_enabled": False,
            "formal_customer_signoff": False,
            "signed_installer_ready": False,
            "internal_fixture_only": True,
        },
        "evidence": {
            key: {"path": _display_path(path), "present": path.exists()}
            for key, path in FILES.items()
        },
        "not_ready_for": [
            "正式客户红队安全签收",
            "真实平台自动外发",
            "成熟商用全渠道客服发布",
            "生产 SLA",
        ],
    }
    _write_json(output_dir / "summary.json", result)
    _write_markdown(DOC_PATH, result)
    return result


if __name__ == "__main__":
    summary = run_nc16_redteam_closure_gate()
    print(json.dumps(summary, ensure_ascii=False, indent=2))
