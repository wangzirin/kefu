#!/usr/bin/env python3
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PHASE = "H2W-10A"
DEFAULT_OUTPUT_DIR = ROOT / "output/p3_06u_26h2w10a_wecom_official_sandbox_readiness"
DOC_PATH = ROOT / "docs/P3-06U-26H2W10A_WECOM_OFFICIAL_SANDBOX_READINESS.md"
MATRIX = ROOT / "docs/channel_autoreply_readiness_matrix.json"
PROVIDER_REGISTRY = ROOT / "backend/app/services/channel_provider_registry.py"
WEBHOOK_VERIFIER = ROOT / "backend/app/services/channel_webhook_verifier.py"
SECRET_STORE = ROOT / "backend/app/services/channel_secret_store.py"
WEBHOOK_TESTS = ROOT / "backend/tests/test_channel_webhooks_api.py"
TRUSTED_INBOUND_TESTS = ROOT / "backend/tests/test_trusted_inbound_worker_api.py"
OUTBOX_SERVICE = ROOT / "backend/app/services/outbox.py"


def _display_path(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def _env_present(*names: str) -> bool:
    return any(bool(os.environ.get(name)) for name in names)


def _write_markdown(path: Path, result: dict[str, Any]) -> None:
    r = result["readiness"]
    lines = [
        "# H2W-10A 企业微信 / 微信客服官方沙箱闭环 readiness",
        "",
        "## 结论",
        "",
        f"- 阶段状态：`{result['status']}`",
        f"- 官方 provider contract：`{str(r['provider_contract_ready']).lower()}`",
        f"- 验签测试：`{str(r['signature_test_ready']).lower()}`",
        f"- 幂等入站测试：`{str(r['idempotent_inbound_ready']).lower()}`",
        f"- 回执记录：`{str(r['receipt_recording_ready']).lower()}`",
        f"- AI 草稿链路：`{str(r['ai_draft_pipeline_ready']).lower()}`",
        f"- 外发默认关闭：`{str(r['external_write_kill_switch_ready']).lower()}`",
        f"- 真实官方沙箱可运行：`{str(r['ready_for_official_sandbox_run']).lower()}`",
        "",
        "## 还缺什么",
        "",
    ]
    if result["blockers"]:
        lines.extend(f"- {item}" for item in result["blockers"])
    else:
        lines.append("- 无")
    lines.extend(
        [
            "",
            "## 企业微信后台需要准备",
            "",
            "1. 已保存微信客服账号，并绑定接待人员。",
            "2. 已有可访问公网 HTTPS 回调地址。",
            "3. 在企业微信后台准备 URL、Token、EncodingAESKey。",
            "4. 自建应用或客服 API 已配置可信 IP。",
            "5. 只做白名单沙箱消息，不面向真实客户开放。",
            "",
            "## 控制台配置手册",
            "",
            "- 企业微信后台选择“微信客服”。",
            "- 进入可调用接口的应用，选择企业内部开发或授权应用。",
            "- 填入后端给出的 HTTPS 回调 URL。",
            "- Token 与 EncodingAESKey 存入客户环境变量或密钥管理，不写入仓库。",
            "- 平台 URL 验证通过后，用个人微信打开客服链接发送测试消息。",
            "- 系统只生成 AI 草稿和回执记录；真实外发仍关闭。",
            "",
            "## 输出",
            "",
            f"- `{result['evidence']['summary_json']['path']}`",
            "",
            "## 边界",
            "",
            "- 本阶段不启用真实外发。",
            "- 本阶段不保存 Token、EncodingAESKey 或客户 secret。",
            "- 本阶段不把“配置模板准备好”写成“已接通”。",
            "- RPA 不进入正式默认交付链。",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_h2w10a_wecom_official_sandbox_readiness(*, output_dir: Path = DEFAULT_OUTPUT_DIR) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    summary_path = output_dir / "summary.json"
    registry = _read(PROVIDER_REGISTRY)
    verifier = _read(WEBHOOK_VERIFIER)
    secret_store = _read(SECRET_STORE)
    webhook_tests = _read(WEBHOOK_TESTS)
    trusted_tests = _read(TRUSTED_INBOUND_TESTS)
    outbox = _read(OUTBOX_SERVICE)
    blockers: list[str] = []
    warnings: list[str] = []

    provider_contract_ready = (
        '"wecom"' in registry
        and "official_sandbox_inbound_only" in registry
        and "external_write_enabled" in registry
        and "False" in registry
    )
    signature_test_ready = (
        "test_wecom_fixture_signature_validates_without_storing_signature_value" in webhook_tests
        and "signature_validated" in webhook_tests
    )
    idempotent_inbound_ready = (
        "test_verified_wecom_message_webhook_replay_does_not_duplicate_message" in webhook_tests
        and "duplicate_ignored" in webhook_tests
    )
    receipt_recording_ready = (
        "delivery-receipts" in webhook_tests
        and "signature_values_stored" in webhook_tests
        and "False" in webhook_tests
    )
    ai_draft_pipeline_ready = (
        "trusted_inbound_message" in trusted_tests
        and "reply_orchestration" in trusted_tests
    )
    external_write_kill_switch_ready = (
        "only dry-run send attempts are supported before a real channel sender exists" in outbox
        and "dry_run" in outbox
    )
    aes_secret_shape_ready = (
        "encoding_aes_key" in secret_store
        and "WECOM" in secret_store
        and "Real customer tokens" in secret_store
    )
    sha1_verify_ready = (
        "_verify_wecom" in verifier
        and "wecom_sha1_token_timestamp_nonce_encrypt" in verifier
    )

    real_sandbox_env_ready = (
        _env_present("WECOM_CORP_ID", "WECOM_SANDBOX_RECEIVER_ID")
        and _env_present("WECOM_TOKEN", "WECOM_SANDBOX_TOKEN")
        and _env_present("WECOM_ENCODING_AES_KEY", "WECOM_SANDBOX_ENCODING_AES_KEY")
    )
    public_callback_env_ready = _env_present("WECOM_CALLBACK_URL", "PUBLIC_HTTPS_CALLBACK_URL")
    trusted_ip_ready = _env_present("WECOM_TRUSTED_IP_CONFIRMED")

    required_checks = {
        "provider_contract_ready": provider_contract_ready,
        "signature_test_ready": signature_test_ready,
        "idempotent_inbound_ready": idempotent_inbound_ready,
        "receipt_recording_ready": receipt_recording_ready,
        "ai_draft_pipeline_ready": ai_draft_pipeline_ready,
        "external_write_kill_switch_ready": external_write_kill_switch_ready,
        "aes_secret_shape_ready": aes_secret_shape_ready,
        "sha1_verify_ready": sha1_verify_ready,
    }
    for key, ready in required_checks.items():
        if not ready:
            blockers.append(f"代码或测试前置条件未满足：{key}")
    if not real_sandbox_env_ready:
        blockers.append("尚未提供真实企业微信沙箱 CorpID/Token/EncodingAESKey 环境配置")
    if not public_callback_env_ready:
        blockers.append("尚未提供公网 HTTPS 回调 URL")
    if not trusted_ip_ready:
        blockers.append("尚未确认企业微信后台可信 IP 配置")

    readiness = {
        **required_checks,
        "real_sandbox_secret_env_ready": real_sandbox_env_ready,
        "public_https_callback_ready": public_callback_env_ready,
        "trusted_ip_ready": trusted_ip_ready,
        "ready_for_official_sandbox_run": not blockers,
        "real_external_write_enabled": False,
    }
    result = {
        "phase": PHASE,
        "status": "passed" if not blockers else "waiting_for_official_sandbox_conditions",
        "readiness": readiness,
        "blockers": blockers,
        "warnings": warnings,
        "evidence": {
            "summary_json": {"path": _display_path(summary_path)},
            "readiness_matrix": {"path": _display_path(MATRIX)},
            "provider_registry": {"path": _display_path(PROVIDER_REGISTRY)},
            "webhook_verifier": {"path": _display_path(WEBHOOK_VERIFIER)},
            "webhook_tests": {"path": _display_path(WEBHOOK_TESTS)},
            "trusted_inbound_tests": {"path": _display_path(TRUSTED_INBOUND_TESTS)},
        },
        "boundaries": {
            "official_backend_authorization_verified": real_sandbox_env_ready and trusted_ip_ready,
            "real_platform_send_performed": False,
            "external_write_kill_switch_opened": False,
            "secret_values_logged": False,
            "rpa_used_as_delivery_path": False,
        },
    }
    _write_json(summary_path, result)
    _write_markdown(DOC_PATH, result)
    return result


def main() -> int:
    result = run_h2w10a_wecom_official_sandbox_readiness()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 1 if result["status"] == "blocked" else 0


if __name__ == "__main__":
    raise SystemExit(main())
