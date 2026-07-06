#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PHASE = "H2W-PILOT5"
SCHEMA_VERSION = "p3-06u-26h2w-pilot5.installer_next_fork_decision.v1"
OUTPUT_DIR = ROOT / "output/p3_06u_26h2w_pilot5_installer_next_fork_decision"
DOC_PATH = ROOT / "docs/P3-06U-26H2W_PILOT5_INSTALLER_NEXT_FORK_DECISION.md"

UPSTREAMS = {
    "pilot0": (
        ROOT / "output/p3_06u_26h2w_pilot0_readiness/summary.json",
        {"pilot_candidate_ready_with_internal_data", "pilot_candidate_ready_with_customer_data"},
    ),
    "pilot3": (
        ROOT / "output/p3_06u_26h2w_pilot3_handoff_archive/summary.json",
        {"pilot_handoff_archive_candidate"},
    ),
    "pilot4": (
        ROOT / "output/p3_06u_26h2w_pilot4_customer_trial_rehearsal/summary.json",
        {"passed_customer_local_trial_rehearsal"},
    ),
    "install2": (
        ROOT / "output/p3_06u_26h2w_install2_native_installer_readiness/summary.json",
        {"native_wrapper_candidate_ready", "installer_plan_ready"},
    ),
}


def _display_path(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _collect_upstreams() -> tuple[dict[str, dict[str, Any]], list[str]]:
    summaries: dict[str, dict[str, Any]] = {}
    blockers: list[str] = []
    for name, (path, accepted_statuses) in UPSTREAMS.items():
        if not path.exists():
            blockers.append(f"{name} summary 缺失：{_display_path(path)}")
            summaries[name] = {"status": "missing"}
            continue
        payload = _read_json(path)
        status = str(payload.get("status") or "")
        summaries[name] = {
            "path": _display_path(path),
            "status": status,
        }
        if status not in accepted_statuses:
            blockers.append(f"{name} 状态不满足：期望 {sorted(accepted_statuses)}，实际 {status}")
        readiness = payload.get("readiness") or {}
        boundaries = payload.get("boundaries") or {}
        if readiness.get("signed_dmg_exe_ready") is True or boundaries.get("signed_dmg_exe_ready") is True:
            blockers.append(f"{name} 越界声明 signed_dmg_exe_ready=true")
        if readiness.get("real_platform_send_ready") is True or boundaries.get("real_platform_send_ready") is True:
            blockers.append(f"{name} 越界声明 real_platform_send_ready=true")
        if payload.get("formal_customer_signoff_performed") is True:
            blockers.append(f"{name} 越界声明 formal_customer_signoff_performed=true")
    return summaries, blockers


def _write_markdown(path: Path, result: dict[str, Any]) -> None:
    lines = [
        "# H2W-PILOT5 安装器下一轮分叉决策",
        "",
        "## 结论",
        "",
        f"- 阶段状态：`{result['status']}`",
        f"- 是否进入安装器专项：`{result['decision']['enter_native_installer_track']}`",
        "- 签名安装包完成：`false`",
        "",
        "## 当前判断",
        "",
        result["decision"]["reason"],
        "",
        "## 下一阶段安装器专项范围",
        "",
    ]
    lines.extend(f"- {item}" for item in result["next_installer_track_scope"])
    lines.extend(
        [
            "",
            "## 不做事项",
            "",
        ]
    )
    lines.extend(f"- {item}" for item in result["not_doing_now"])
    if result["blockers"]:
        lines.extend(["", "## 阻断项", ""])
        lines.extend(f"- {item}" for item in result["blockers"])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_h2w_pilot5_installer_next_fork_decision() -> dict[str, Any]:
    summaries, blockers = _collect_upstreams()
    enter_installer_track = not blockers
    result = {
        "schema_version": SCHEMA_VERSION,
        "phase": PHASE,
        "status": "blocked" if blockers else "installer_next_fork_decision_ready",
        "upstreams": summaries,
        "decision": {
            "enter_native_installer_track": enter_installer_track,
            "reason": (
                "PILOT0、PILOT3、PILOT4 与 INSTALL2 均具备候选证据，可以进入下一阶段原生安装器专项。"
                if enter_installer_track
                else "上游证据尚未完整，暂不进入签名安装器或桌面安装包承诺。"
            ),
        },
        "next_installer_track_scope": [
            "macOS .app 包装结构与图标、版本文件、日志目录",
            "Windows PowerShell / 快捷方式包装与启动前预检",
            "升级前自动备份、更新失败回滚、卸载清理说明",
            "Apple / Windows 代码签名前置清单和兼容性 QA",
            "安装后健康检查，确认运行版本、端口和关键接口来自新包",
        ],
        "not_doing_now": [
            "不写正式 dmg/exe 已完成",
            "不做代码签名完成声明",
            "不启用真实外发",
            "不静默更新客户电脑",
            "不远控客户电脑",
            "不把内部演练写成客户正式验收",
        ],
        "readiness": {
            "native_installer_track_can_start": enter_installer_track,
            "signed_dmg_exe_ready": False,
            "desktop_installer_ready": False,
            "real_platform_send_ready": False,
            "formal_customer_signoff_ready": False,
        },
        "blockers": blockers,
    }
    _write_json(OUTPUT_DIR / "summary.json", result)
    _write_markdown(DOC_PATH, result)
    return result


def main() -> int:
    result = run_h2w_pilot5_installer_next_fork_decision()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] != "blocked" else 1


if __name__ == "__main__":
    raise SystemExit(main())
