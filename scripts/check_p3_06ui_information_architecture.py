#!/usr/bin/env python3
"""Static readiness checks for P3-06UI information architecture."""

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read_text(relative_path: str) -> str:
    return (ROOT / relative_path).read_text(encoding="utf-8")


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    navigation = read_text("frontend/src/data/navigation.ts")
    app = read_text("frontend/src/App.tsx")
    styles = read_text("frontend/src/styles.css")
    doc = read_text("docs/P3-06UI_INFORMATION_ARCHITECTURE.md")

    expected_groups = [
        "总览",
        "工作台",
        "客户",
        "知识运营",
        "质量复盘",
        "渠道接入",
        "管理运维",
    ]
    expected_children = [
        "运营总览",
        "多渠道对话台",
        "会话收件箱",
        "人工审核",
        "待发送草稿",
        "工单/SLA",
        "联系人中心",
        "线索跟进",
        "知识库运营",
        "知识缺口",
        "知识评测",
        "质量诊断",
        "连接器状态",
        "运维与告警",
        "模型路由",
        "系统设置",
    ]

    require("navigationGroups" in navigation, "navigationGroups is missing from navigation data")
    require("export const navigation = navigationGroups.flatMap" in navigation, "flat navigation compatibility export is missing")
    require('count: "P3-06UI"' not in navigation, "customer-facing navigation must not show P3-06UI stage marker")
    require('count: "P3-06F"' not in navigation, "customer-facing navigation must not show P3-06F stage marker")
    require('count: "规划"' not in navigation, "customer-facing navigation must not show planning marker")
    require('count: "今日"' in navigation, "overview navigation should use customer-facing label")
    require("告警中心" not in navigation, "alert rules must not be promoted to a new top-level alert center")

    for group in expected_groups:
      require(f'label: "{group}"' in navigation, f"navigation group missing: {group}")
      require(group in doc, f"documentation missing group: {group}")

    for child in expected_children:
      require(f'label: "{child}"' in navigation, f"navigation child missing: {child}")

    require(
        "navigationGroups.map" in app or "visibleNavigationGroups.map" in app,
        "App sidebar is not rendering grouped navigation",
    )
    require("nav-group-link" in app, "App sidebar is missing group link markup")
    require("nav-child-list" in app, "App sidebar is missing child list markup")

    for class_name in ["nav-group", "nav-group-link", "nav-child-list"]:
      require(f".{class_name}" in styles, f"CSS class missing: {class_name}")

    for phrase in ["7 个工作域", "不改后端业务逻辑", "不启用真实外发", "P3-06UI 第二片"]:
      require(phrase in doc, f"documentation missing phrase: {phrase}")

    print("P3-06UI information architecture checks passed.")


if __name__ == "__main__":
    main()
