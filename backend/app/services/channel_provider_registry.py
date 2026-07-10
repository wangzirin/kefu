from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class ChannelProviderContract:
    provider: str
    display_name: str
    supported_channel_types: list[str]
    default_signature_mode: str
    webhook_path_template: str
    inbound_event_types: list[str]
    capabilities: dict[str, Any]
    verification_contract: dict[str, Any]
    inbound_event_contract: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def normalize_provider(provider: str) -> str:
    return provider.strip().lower().replace("-", "_")


_PROVIDER_CONTRACTS = {
    "wechat_kf": ChannelProviderContract(
        provider="wechat_kf",
        display_name="微信客服",
        supported_channel_types=["wechat_kf", "wechat_customer_service"],
        default_signature_mode="wechat_kf_token_aeskey",
        webhook_path_template="/api/webhooks/wechat-kf/channels/{channel_id}",
        inbound_event_types=["verification_echo", "message", "customer_event"],
        capabilities={
            "receive_webhook": True,
            "external_write_enabled": True,
            "requires_official_authorization": True,
            "supports_encrypted_payload": True,
            "supports_delivery_receipt": True,
            "required_public_fields": ["enterprise_name", "corp_id", "callback_url"],
            "required_secret_fields": ["token", "encoding_aes_key", "app_secret"],
        },
        verification_contract={
            "production_status": "official_sandbox_inbound_only",
            "requires_secret_store": True,
            "required_query_keys": ["msg_signature", "timestamp", "nonce"],
            "required_secret_fields": ["token", "encoding_aes_key", "app_secret"],
            "required_public_fields": ["enterprise_name", "corp_id", "callback_url"],
            "validated_in_current_stage": True,
            "fixture_validation_in_current_stage": True,
            "notes": "绑定阶段支持微信客服 URL 验证、AES 解密和可信入站消息创建；open_kfid 可在入站事件或账号同步后补齐，文本外发仍受账号标识、全局、渠道和白名单门禁控制。",
        },
        inbound_event_contract={
            "raw_payload_retained": True,
            "signature_values_stored": False,
            "parsed_event_status": "trusted_inbound_message_created_when_signature_decrypt_and_content_are_valid",
            "trusted_message_creation": True,
        },
    ),
    "wecom": ChannelProviderContract(
        provider="wecom",
        display_name="企业微信客服",
        supported_channel_types=["wecom", "enterprise_wechat"],
        default_signature_mode="wecom_token_aeskey",
        webhook_path_template="/api/webhooks/wecom/channels/{channel_id}",
        inbound_event_types=["verification_echo", "message", "delivery_receipt", "customer_event"],
        capabilities={
            "receive_webhook": True,
            "external_write_enabled": True,
            "requires_official_authorization": True,
            "supports_encrypted_payload": True,
            "supports_delivery_receipt": True,
            "required_public_fields": ["enterprise_name", "corp_id", "agent_id", "callback_url"],
        },
        verification_contract={
            "production_status": "official_sandbox_inbound_only",
            "requires_secret_store": True,
            "required_query_keys": ["msg_signature", "timestamp", "nonce"],
            "required_secret_fields": ["token", "encoding_aes_key", "app_secret"],
            "required_public_fields": ["enterprise_name", "corp_id", "agent_id", "callback_url"],
            "validated_in_current_stage": True,
            "fixture_validation_in_current_stage": True,
            "notes": "P3-05E 已支持 env secret 引用、官方 URL 验证、AES 解密、XML 消息解析和可信入站消息创建；真实 access_token、发送 API、可信 IP、限流和外部写入仍未打开。",
        },
        inbound_event_contract={
            "raw_payload_retained": True,
            "signature_values_stored": False,
            "parsed_event_status": "trusted_inbound_message_created_when_signature_decrypt_and_content_are_valid",
            "trusted_message_creation": True,
        },
    ),
    "wechat_official_account": ChannelProviderContract(
        provider="wechat_official_account",
        display_name="微信公众号",
        supported_channel_types=["wechat_official_account", "wechat_mp", "mp_weixin"],
        default_signature_mode="wechat_token",
        webhook_path_template="/api/webhooks/wechat-official-account/channels/{channel_id}",
        inbound_event_types=["verification_echo", "message", "delivery_receipt", "customer_event"],
        capabilities={
            "receive_webhook": True,
            "external_write_enabled": False,
            "requires_official_authorization": True,
            "supports_encrypted_payload": True,
            "supports_delivery_receipt": False,
            "required_public_fields": ["account_name", "app_id", "server_url"],
        },
        verification_contract={
            "production_status": "skeleton_only",
            "requires_secret_store": True,
            "required_query_keys": ["signature", "timestamp", "nonce"],
            "required_secret_fields": ["token", "encoding_aes_key_optional"],
            "required_public_fields": ["account_name", "app_id", "server_url"],
            "validated_in_current_stage": False,
            "fixture_validation_in_current_stage": True,
            "notes": "P2-13 已支持开发 fixture 的公众号明文模式 SHA1 签名验证；安全模式解密、幂等和可信消息创建仍未完成。",
        },
        inbound_event_contract={
            "raw_payload_retained": True,
            "signature_values_stored": False,
            "parsed_event_status": "placeholder_only",
            "trusted_message_creation": False,
        },
    ),
    "website": ChannelProviderContract(
        provider="website",
        display_name="官网客服组件",
        supported_channel_types=["website", "web"],
        default_signature_mode="website_hmac_sha256",
        webhook_path_template="/api/webhooks/website/channels/{channel_id}",
        inbound_event_types=["message", "delivery_receipt", "customer_event"],
        capabilities={
            "receive_webhook": True,
            "external_write_enabled": False,
            "requires_official_authorization": False,
            "supports_encrypted_payload": False,
            "supports_delivery_receipt": True,
        },
        verification_contract={
            "production_status": "skeleton_only",
            "requires_secret_store": True,
            "required_query_keys": ["signature", "timestamp", "nonce"],
            "required_secret_fields": ["webhook_signing_secret"],
            "validated_in_current_stage": True,
            "fixture_validation_in_current_stage": True,
            "notes": "P3-04 已支持开发 fixture 的 HMAC-SHA256 验证和可信消息创建；生产密钥轮换、重放 nonce 存储和真实外发仍未完成。",
        },
        inbound_event_contract={
            "raw_payload_retained": True,
            "signature_values_stored": False,
            "parsed_event_status": "trusted_inbound_message_created_when_signature_and_content_are_valid",
            "trusted_message_creation": True,
        },
    ),
    "wechat_miniapp": ChannelProviderContract(
        provider="wechat_miniapp",
        display_name="微信小程序",
        supported_channel_types=["wechat_miniapp", "miniapp"],
        default_signature_mode="wechat_token",
        webhook_path_template="/api/webhooks/wechat-miniapp/channels/{channel_id}",
        inbound_event_types=["verification_echo", "message", "customer_event"],
        capabilities={
            "receive_webhook": True,
            "external_write_enabled": False,
            "requires_official_authorization": True,
            "supports_encrypted_payload": True,
            "supports_delivery_receipt": False,
            "required_public_fields": ["miniapp_name", "app_id", "server_url"],
            "required_secret_fields": ["token", "encoding_aes_key", "app_secret"],
        },
        verification_contract={
            "production_status": "self_service_configuration_skeleton",
            "requires_secret_store": True,
            "required_query_keys": ["signature", "timestamp", "nonce"],
            "required_secret_fields": ["token", "encoding_aes_key", "app_secret"],
            "required_public_fields": ["miniapp_name", "app_id", "server_url"],
            "validated_in_current_stage": False,
            "fixture_validation_in_current_stage": True,
            "notes": "小程序作为咨询入口配置；主动发送能力按微信平台限制后续单独验收。",
        },
        inbound_event_contract={
            "raw_payload_retained": True,
            "signature_values_stored": False,
            "parsed_event_status": "configuration_skeleton",
            "trusted_message_creation": False,
        },
    ),
}

_PROVIDER_ALIASES = {
    "wechat_official_account": "wechat_official_account",
    "wechat_kf": "wechat_kf",
    "wechat-kf": "wechat_kf",
    "wechat_customer_service": "wechat_kf",
    "weixin_kf": "wechat_kf",
    "wechat-miniapp": "wechat_miniapp",
    "wechat_miniapp": "wechat_miniapp",
    "miniapp": "wechat_miniapp",
    "wechat_mp": "wechat_official_account",
    "mp_weixin": "wechat_official_account",
    "weixin_mp": "wechat_official_account",
    "wechat-official-account": "wechat_official_account",
    "enterprise_wechat": "wecom",
    "qiye_weixin": "wecom",
    "wecom": "wecom",
    "website": "website",
    "web": "website",
}


def get_channel_provider_contract(provider: str) -> dict[str, Any] | None:
    normalized = normalize_provider(provider)
    canonical = _PROVIDER_ALIASES.get(normalized, normalized)
    contract = _PROVIDER_CONTRACTS.get(canonical)
    return contract.to_dict() if contract is not None else None


def list_channel_provider_contracts() -> list[dict[str, Any]]:
    return [_PROVIDER_CONTRACTS[key].to_dict() for key in sorted(_PROVIDER_CONTRACTS)]
