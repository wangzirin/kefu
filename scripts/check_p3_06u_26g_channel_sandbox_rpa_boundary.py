#!/usr/bin/env python3
"""Static checks for P3-06U-26G channel sandbox and RPA draft-only boundary."""

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read_text(relative_path: str) -> str:
    return (ROOT / relative_path).read_text(encoding="utf-8")


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def require_all(text: str, snippets: list[str], label: str) -> None:
    for snippet in snippets:
        require(snippet in text, f"{label} missing required snippet: {snippet}")


def main() -> None:
    doc = read_text("docs/P3-06U-26G_CHANNEL_SANDBOX_AND_RPA_BOUNDARY.md")
    channel_panel = read_text("frontend/src/components/channels/ChannelConnectorCenterPanel.tsx")
    rpa_panel = read_text("frontend/src/components/rpa/RpaCopilotLabPanel.tsx")
    styles = read_text("frontend/src/styles.css")
    master_plan = read_text("docs/P3-06U-26_ENGINEERING_OPTIMIZATION_MASTER_PLAN.md")

    require_all(
        doc,
        [
            "# P3-06U-26G 渠道官方 sandbox 与 RPA draft-only 边界",
            "RPA 不进入正式默认交付链",
            "draft-only",
            "真实外发继续关闭",
            "官方授权",
            "测试白名单",
            "回执",
            "失败重试",
            "审计闭环",
            "个人号外挂",
            "Hook",
            "群控",
            "Cookie 复用",
            "P3-06U-26H",
        ],
        "26G doc",
    )
    for channel_name in ["企业微信 / 微信客服", "微信公众号", "抖音 / 抖店", "小红书", "淘宝 / 天猫 / 京东 / 拼多多"]:
        require(channel_name in doc, f"26G doc missing channel matrix entry: {channel_name}")

    require_all(
        channel_panel,
        [
            'data-channel-sandbox-priority="p3-06u-26g"',
            "CHANNEL_SANDBOX_PRIORITIES",
            "官方 sandbox 优先级",
            "RPA draft-only",
            "RPA 不进入正式默认交付链",
            "真实外发继续关闭",
            "个人微信外挂",
            "网页私信只能做 draft-only 研究",
            "商家后台 RPA 只允许草稿和证据采集",
        ],
        "channel connector panel",
    )

    require_all(
        rpa_panel,
        [
            'data-rpa-draft-only-boundary="p3-06u-26g"',
            "RPA 研究线：draft-only",
            "只允许读取页面上下文、生成草稿、填框和证据采集",
            "RPA 不进入正式默认交付链",
            "真实外发继续关闭",
        ],
        "RPA lab panel",
    )

    require_all(
        styles,
        [
            ".channel-access-route-matrix",
            ".channel-access-route-row",
            ".rpa-boundary-strip",
        ],
        "styles",
    )

    require_all(
        master_plan,
        [
            "### P3-06U-26G：渠道官方 sandbox 优先级和 RPA draft-only 研究边界固化",
            "RPA 不进入正式默认交付链",
            "非官方模拟点击被写成自动回复能力",
        ],
        "master plan",
    )

    forbidden_formal_claims = [
        "RPA 进入正式默认交付链",
        "个人号外挂作为正式交付",
        "群控作为正式交付",
        "Cookie 复用作为正式交付",
        "真实外发已开启",
        "抖音商家客服已经接通",
    ]
    combined = "\n".join([doc, channel_panel, rpa_panel])
    for forbidden in forbidden_formal_claims:
        require(forbidden not in combined, f"forbidden claim should not appear: {forbidden}")

    print("P3-06U-26G channel sandbox and RPA boundary check passed.")


if __name__ == "__main__":
    main()
