#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PHASE = "H2W-PACK3"
DEFAULT_OUTPUT_DIR = ROOT / "output/p3_06u_26h2w_pack3_local_pilot_candidate_readiness"
DOC_PATH = ROOT / "docs/P3-06U-26H2W_PACK3_LOCAL_PILOT_CANDIDATE_READINESS.md"

PACK2_SUMMARY = ROOT / "output/p3_06u_26h2w_pack2_full_stack_startup_rehearsal/summary.json"
PACK1_SUMMARY = ROOT / "output/p3_06u_26h2w_pack1_local_delivery_rehearsal/summary.json"
FE3_SUMMARY = ROOT / "output/p3_06u_26h2w_fe3_frontend_browser_workflow_qa/summary.json"
H2W7D_RUNTIME_SUMMARY = ROOT / "output/p3_06u_26h2w7d_runtime_pgvector_rehearsal/summary.json"
MODEL1_SUMMARY = ROOT / "output/p3_06u_26h2w_model1_bailian_cost_sample/summary.json"
TRIAL1_SUMMARY = ROOT / "output/p3_06u_26h2w_trial1_internal_100q_rehearsal_report/summary.json"
CUSTOMER_ENV = ROOT / "deploy/customer.env.example"
PILOT_COMPOSE = ROOT / "deploy/docker-compose.pilot.yml"


def _display_path(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _summary_status(path: Path) -> str:
    if not path.exists():
        return "missing"
    try:
        return str(_read_json(path).get("status", "unknown"))
    except json.JSONDecodeError:
        return "invalid_json"


def _env_map(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.exists():
        return values
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def _safe_customer_env(path: Path) -> tuple[bool, list[str]]:
    blockers: list[str] = []
    values = _env_map(path)
    if not path.exists():
        return False, [f"缺少客户环境模板：{_display_path(path)}"]
    if values.get("STANDARD_OPS_DEV_BOOTSTRAP_ENABLED") != "false":
        blockers.append("客户环境模板必须关闭 STANDARD_OPS_DEV_BOOTSTRAP_ENABLED")
    if values.get("OUTBOX_EXTERNAL_WRITE_ENABLED") != "false":
        blockers.append("客户环境模板必须关闭 OUTBOX_EXTERNAL_WRITE_ENABLED")
    if values.get("ADMIN_BOOTSTRAP_PASSWORD"):
        blockers.append("客户环境模板不得内置 ADMIN_BOOTSTRAP_PASSWORD")
    if values.get("KNOWLEDGE_VECTOR_STORE") != "postgres_pgvector_store_v1":
        blockers.append("客户环境模板必须使用 postgres_pgvector_store_v1 作为生产候选知识检索")
    return not blockers, blockers


def _safe_pilot_compose(path: Path) -> tuple[bool, list[str]]:
    if not path.exists():
        return False, [f"缺少 pilot compose：{_display_path(path)}"]
    text = path.read_text(encoding="utf-8")
    required = [
        'STANDARD_OPS_DEV_BOOTSTRAP_ENABLED: "false"',
        'OUTBOX_EXTERNAL_WRITE_ENABLED: "false"',
        'TRUSTED_INBOUND_WORKER_ENABLED: "false"',
    ]
    missing = [marker for marker in required if marker not in text]
    return not missing, [f"pilot compose 缺少安全开关：{marker}" for marker in missing]


def _assert_boundary_false(path: Path, key: str) -> bool:
    if not path.exists():
        return False
    data = _read_json(path)
    return data.get("boundaries", {}).get(key) is False


def _write_markdown(path: Path, result: dict[str, Any]) -> None:
    readiness = result["readiness"]
    lines = [
        "# H2W-PACK3 本地受控试点封版候选总门禁",
        "",
        "## 结论",
        "",
        f"- 阶段状态：`{result['status']}`",
        f"- 本地受控试点候选：`{str(readiness['ready_for_local_controlled_pilot_candidate']).lower()}`",
        f"- 正式客户签收：`{str(readiness['formal_customer_signoff_ready']).lower()}`",
        f"- 真实平台外发：`{str(readiness['real_platform_send_ready']).lower()}`",
        f"- 企业渠道接入：`{str(readiness['enterprise_channel_ready']).lower()}`",
        "",
        "## 证据总表",
        "",
        "| 证据 | 期望状态 | 当前状态 | 通过 |",
        "|---|---|---:|---:|",
    ]
    for item in result["evidence_matrix"]:
        lines.append(
            f"| {item['name']} | `{item['expected']}` | `{item['actual']}` | `{str(item['passed']).lower()}` |"
        )
    lines.extend(["", "## 阻断项", ""])
    lines.extend([f"- {item}" for item in result["blockers"]] or ["- 无"])
    lines.extend(["", "## 不可对外承诺", ""])
    lines.extend([f"- {item}" for item in result["not_ready_for"]])
    lines.extend(["", "## 下一步建议", ""])
    lines.extend([f"- {item}" for item in result["next_recommended_steps"]])
    lines.extend(
        [
            "",
            "## 固定边界",
            "",
            "- 内部 100 题只代表内部演练，不代表客户真实题库。",
            "- 当前不是正式客户准确率签收。",
            "- 真实外发继续关闭。",
            "- 企业微信、微信客服、抖音、淘宝、京东、拼多多等真实渠道接入暂停。",
            "- RPA 不进入正式默认交付链。",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_h2w_pack3_local_pilot_candidate_readiness(
    *,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    doc_path: Path = DOC_PATH,
    pack2_summary: Path = PACK2_SUMMARY,
    pack1_summary: Path = PACK1_SUMMARY,
    fe3_summary: Path = FE3_SUMMARY,
    h2w7d_runtime_summary: Path = H2W7D_RUNTIME_SUMMARY,
    model1_summary: Path = MODEL1_SUMMARY,
    trial1_summary: Path = TRIAL1_SUMMARY,
    customer_env: Path = CUSTOMER_ENV,
    pilot_compose: Path = PILOT_COMPOSE,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    summary_path = output_dir / "summary.json"
    blockers: list[str] = []
    warnings: list[str] = []

    expected_statuses = [
        ("PACK2 全栈首启", pack2_summary, "passed_full_stack_backend_startup_rehearsal"),
        ("PACK1 本地交付候选", pack1_summary, "passed_local_package_runtime_rehearsal_ready"),
        ("FE3 前端真实工作流", fe3_summary, "passed"),
        ("7D pgvector runtime", h2w7d_runtime_summary, "ready_for_runtime_rehearsal"),
        ("MODEL1 百炼小样本成本", model1_summary, "passed_real_small_sample_cost_rehearsal"),
        ("TRIAL1 内部 100 题演练", trial1_summary, "passed_internal_rehearsal_report"),
    ]
    evidence_matrix: list[dict[str, Any]] = []
    for name, path, expected in expected_statuses:
        actual = _summary_status(path)
        passed = actual == expected
        evidence_matrix.append(
            {
                "name": name,
                "path": _display_path(path),
                "expected": expected,
                "actual": actual,
                "passed": passed,
            }
        )
        if not passed:
            blockers.append(f"{name} 未达到期望状态：期望 {expected}，实际 {actual}")

    customer_env_safe, env_blockers = _safe_customer_env(customer_env)
    pilot_compose_safe, compose_blockers = _safe_pilot_compose(pilot_compose)
    blockers.extend(env_blockers)
    blockers.extend(compose_blockers)

    pack2_no_send = _assert_boundary_false(pack2_summary, "real_platform_send_performed")
    pack2_no_signoff = _assert_boundary_false(pack2_summary, "formal_customer_signoff_performed")
    pack2_no_dev_bootstrap = _assert_boundary_false(pack2_summary, "development_bootstrap_allowed")
    trial1_no_customer_report = _assert_boundary_false(trial1_summary, "customer_quality_report_candidate")
    trial1_no_formal_signoff = _assert_boundary_false(trial1_summary, "formal_accuracy_signoff_performed")
    trial1_internal_boundary = bool(
        trial1_summary.exists()
        and _read_json(trial1_summary).get("boundaries", {}).get("internal_rehearsal_not_customer_signoff") is True
    )
    model_no_send = _assert_boundary_false(model1_summary, "real_platform_send_performed")

    boundary_checks = {
        "pack2_no_real_platform_send": pack2_no_send,
        "pack2_no_formal_customer_signoff": pack2_no_signoff,
        "pack2_development_bootstrap_disabled": pack2_no_dev_bootstrap,
        "trial1_customer_quality_report_not_ready": trial1_no_customer_report,
        "trial1_formal_signoff_not_performed": trial1_no_formal_signoff,
        "trial1_marked_internal_rehearsal": trial1_internal_boundary,
        "model1_no_real_platform_send": model_no_send,
        "customer_env_safe": customer_env_safe,
        "pilot_compose_safe": pilot_compose_safe,
    }
    for key, passed in boundary_checks.items():
        if not passed:
            blockers.append(f"安全边界未通过：{key}")

    if trial1_summary.exists():
        trial = _read_json(trial1_summary)
        metrics = trial.get("metrics", {})
        if metrics.get("dataset_source_type") != "internal_synthetic_rehearsal":
            blockers.append("TRIAL1 题库来源必须保持 internal_synthetic_rehearsal，不能伪装成客户题库")
        if metrics.get("question_count") != 100:
            warnings.append(f"TRIAL1 内部题库数量不是 100：{metrics.get('question_count')}")

    ready = not blockers
    status = "ready_for_local_controlled_pilot_candidate" if ready else "blocked"
    result = {
        "phase": PHASE,
        "status": status,
        "readiness": {
            "ready_for_local_controlled_pilot_candidate": ready,
            "formal_customer_signoff_ready": False,
            "real_platform_send_ready": False,
            "enterprise_channel_ready": False,
            "desktop_installer_ready": False,
            "customer_specific_knowledge_ready": False,
        },
        "evidence_matrix": evidence_matrix,
        "boundary_checks": boundary_checks,
        "blockers": blockers,
        "warnings": warnings,
        "not_ready_for": [
            "正式客户准确率签收",
            "真实平台自动外发",
            "企业微信/微信客服/抖音/淘宝/京东/拼多多真实渠道上线",
            "客户专属知识库验收",
            "完整桌面安装器或一键安装包",
            "生产环境监控、告警和长期运维 SLA",
        ],
        "next_recommended_steps": [
            "H2W-PACK4：制作客户本地试点交付清单和一键启动 rehearsal，不打开真实外发。",
            "H2W-FE4：对封版候选 UI 做最后一轮客户视角点击验收，隐藏或禁用仍无真实动作的按钮。",
            "H2W-KB1：把内部 100 题替换为某个共创客户授权后的真实脱敏题库，再生成客户质量报告候选。",
        ],
        "evidence": {
            "summary_json": {"path": _display_path(summary_path)},
            "markdown": {"path": _display_path(doc_path)},
        },
        "boundaries": {
            "internal_rehearsal_not_customer_signoff": True,
            "real_platform_send_performed": False,
            "enterprise_channel_scope_included": False,
            "rpa_formal_delivery_included": False,
            "formal_customer_signoff_performed": False,
        },
    }
    _write_json(summary_path, result)
    _write_markdown(doc_path, result)
    return result


def main() -> int:
    result = run_h2w_pack3_local_pilot_candidate_readiness()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] == "ready_for_local_controlled_pilot_candidate" else 1


if __name__ == "__main__":
    raise SystemExit(main())
