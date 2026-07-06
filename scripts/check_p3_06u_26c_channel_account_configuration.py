#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


CHECKS = [
    (
        "frontend/src/api/client.ts",
        [
            "export interface Channel",
            "export interface ChannelAccountPayload",
            "export async function listTenantChannels",
            "export async function configureChannelAccount",
            "/api/tenants/${tenantId}/channels",
            "/api/channels/${channelId}/channel-accounts",
        ],
    ),
    (
        "frontend/src/App.tsx",
        [
            "type ChannelAccountState",
            "const [channelAccountState, setChannelAccountState]",
            "Promise.all([listTenantChannels(tenantId, token), listChannelAccounts(tenantId, token)])",
            "handleConfigureChannelAccount",
            "channelAccountState={channelAccountState}",
            "onConfigureChannelAccount",
            "onRefreshChannelAccounts",
            "当前为预览样例；正式配置需登录后读取 channel_accounts。",
        ],
    ),
    (
        "frontend/src/components/channels/ChannelConnectorCenterPanel.tsx",
        [
            'data-channel-account-manager="p3-06u-26c"',
            'data-channel-account-list="server"',
            'data-channel-account-form="server"',
            'data-channel-account-refresh="p3-06u-26c"',
            "渠道账号 / 店铺管理",
            "服务端 channel_accounts 配置",
            "真实外发继续关闭",
            "external_write: \"disabled_by_design\"",
            "Secret、Token、Cookie",
        ],
    ),
    (
        "frontend/src/styles.css",
        [
            ".channel-account-manager",
            ".channel-account-layout",
            ".channel-account-list-card",
            ".channel-account-form",
            ".channel-account-table",
            ".channel-account-row",
            ".channel-account-empty",
        ],
    ),
    (
        "docs/P3-06U-26C_CHANNEL_ACCOUNT_CONFIGURATION_PANEL.md",
        [
            "# P3-06U-26C 渠道账号/店铺配置面板",
            "真实外发继续关闭",
            "不保存 Secret、Token、Cookie",
            "GET /api/tenants/{tenant_id}/channels",
            "GET /api/tenants/{tenant_id}/channel-accounts",
            "POST /api/channels/{channel_id}/channel-accounts",
            "P3-06U-26D",
        ],
    ),
]


def main() -> int:
    failures: list[str] = []
    for relative_path, needles in CHECKS:
        path = ROOT / relative_path
        if not path.exists():
            failures.append(f"missing file: {relative_path}")
            continue
        content = path.read_text(encoding="utf-8")
        for needle in needles:
            if needle not in content:
                failures.append(f"{relative_path}: missing {needle!r}")

    component = (ROOT / "frontend/src/components/channels/ChannelConnectorCenterPanel.tsx").read_text(encoding="utf-8")
    forbidden_needles = [
        "access_token:",
        "secret_key:",
        "cookie:",
        "password:",
        "真实外发已开启",
    ]
    for needle in forbidden_needles:
        if needle in component:
            failures.append(f"component contains forbidden sensitive/write-open marker: {needle!r}")

    if failures:
        print("P3-06U-26C static check failed:")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print("P3-06U-26C static check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
