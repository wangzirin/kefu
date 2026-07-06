#!/usr/bin/env python3
"""Static checks for P3-06U-08 channel connector center productization."""

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read_text(relative_path: str) -> str:
    return (ROOT / relative_path).read_text(encoding="utf-8")


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    app = read_text("frontend/src/App.tsx")
    channel_panel = read_text("frontend/src/components/channels/ChannelConnectorCenterPanel.tsx")
    styles = read_text("frontend/src/styles.css")
    doc = read_text("docs/P3-06U-08_CHANNEL_CONNECTOR_CENTER_PRODUCTIZATION.md")
    browser_script = read_text("scripts/check_p3_06u_08_channel_connector_center.mjs")

    require(
        'from "./components/channels/ChannelConnectorCenterPanel"' in app,
        "App should import the channel connector center component after extraction",
    )
    require(
        "export function ChannelConnectorCenterPanel" in channel_panel,
        "channel connector center should be exported from its own component file",
    )

    for snippet in [
        "ChannelConnectorCenterPanel",
        "ChannelConnectorStepStatus",
        'data-channel-connector-smoke="center"',
        'data-channel-connector-primary="wecom"',
        "data-channel-connector-step",
        "data-channel-connector-config",
        "data-channel-official-only",
        "回调 URL 待配置",
        "URL 验证通过",
        "已收到入站消息",
        "已生成 AI 草稿",
        "已进入人工审核",
        "白名单发送测试通过",
        "公网 HTTPS 回调 URL",
        "EncodingAESKey",
        "可信 IP",
        "已隐藏明文",
        "不使用个人号外挂",
        "Hook",
        "模拟点击",
        "商家后台群控",
        "公众号",
        "抖音 / 抖店",
        "小红书",
        "淘宝 / 天猫",
        "京东 / 拼多多",
    ]:
        require(snippet in channel_panel, f"channel connector component missing snippet: {snippet}")

    for snippet in [
        ".channel-connector-center",
        ".channel-primary-card",
        ".channel-setup-track",
        ".channel-setup-step",
        ".channel-config-grid",
        ".channel-official-grid",
        ".channel-status-dot.urgent",
        "@media (max-width: 1180px)",
        "@media (max-width: 960px)",
        "@media (max-width: 560px)",
    ]:
        require(snippet in styles, f"styles missing channel connector class or breakpoint: {snippet}")

    for phrase in [
        "# P3-06U-08 渠道连接器中心实用化",
        "不新增后端字段",
        "不打开真实外发",
        "Token 和 EncodingAESKey 只显示 secret 引用",
        "官方授权前置条件",
        "未接入状态",
        "P3-06U-09",
    ]:
        require(phrase in doc, f"documentation missing phrase: {phrase}")

    for snippet in [
        "data-channel-connector-smoke",
        "data-channel-connector-primary",
        "data-channel-connector-step",
        "data-channel-connector-config",
        "data-channel-official-only",
        "desktop-1440",
        "desktop-900",
        "mobile-390",
        "output/p3_06u_08_channel_connector_center",
        "summary.json",
    ]:
        require(snippet in browser_script, f"browser smoke missing snippet: {snippet}")

    print("P3-06U-08 channel connector center static checks passed.")


if __name__ == "__main__":
    main()
