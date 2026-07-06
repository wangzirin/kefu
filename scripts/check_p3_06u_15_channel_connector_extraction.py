#!/usr/bin/env python3
"""Static checks for P3-06U-15 channel connector center extraction."""

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
    doc = read_text("docs/P3-06U-15_CHANNEL_CONNECTOR_CENTER_EXTRACTION.md")

    require(
        'from "./components/channels/ChannelConnectorCenterPanel"' in app,
        "App should import ChannelConnectorCenterPanel from components/channels",
    )
    require(
        "function ChannelConnectorCenterPanel(" not in app,
        "App should not define ChannelConnectorCenterPanel after extraction",
    )
    require(
        "function buildChannelConnectorCards(" not in app,
        "App should not keep channel connector card builder after extraction",
    )
    require(
        "interface ChannelConnectorCard" not in app,
        "App should not keep channel connector-only card types",
    )
    require(
        "export function ChannelConnectorCenterPanel" in channel_panel,
        "ChannelConnectorCenterPanel should be exported from its own file",
    )

    for snippet in [
        "type ChannelConnectorStepStatus",
        "interface ChannelConnectorCard",
        "function buildChannelConnectorCards",
        'data-channel-connector-smoke="center"',
        'data-channel-connector-primary="wecom"',
        "data-channel-connector-step",
        "data-channel-connector-config",
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

    for phrase in [
        "# P3-06U-15 渠道连接器中心组件拆分",
        "行为不变，结构变清楚",
        "没有新增真实外发",
        "frontend/src/components/channels/ChannelConnectorCenterPanel.tsx",
        "P3-06U-08",
        "npm run typecheck",
    ]:
        require(phrase in doc, f"U15 documentation missing phrase: {phrase}")

    require(len(app.splitlines()) < 10900, "App.tsx should shrink after channel connector extraction")

    print("P3-06U-15 channel connector extraction static checks passed.")


if __name__ == "__main__":
    main()
