from __future__ import annotations

import base64
from dataclasses import dataclass
import hashlib
import struct
import xml.etree.ElementTree as ET

from Crypto.Cipher import AES


class WecomCallbackCryptoError(ValueError):
    pass


@dataclass(frozen=True)
class WecomDecryptResult:
    plaintext: str
    receiver_id: str


def wecom_sha1_signature(*, token: str, timestamp: str, nonce: str, encrypted_text: str) -> str:
    return hashlib.sha1("".join(sorted([token, timestamp, nonce, encrypted_text])).encode("utf-8")).hexdigest()


def _decode_encoding_aes_key(encoding_aes_key: str) -> bytes:
    key_text = encoding_aes_key.strip()
    if len(key_text) != 43:
        raise WecomCallbackCryptoError("EncodingAESKey must be 43 characters")
    try:
        key = base64.b64decode(key_text + "=", validate=True)
    except Exception as exc:  # noqa: BLE001 - normalize third-party/base64 errors.
        raise WecomCallbackCryptoError("EncodingAESKey is not valid base64") from exc
    if len(key) != 32:
        raise WecomCallbackCryptoError("EncodingAESKey must decode to 32 bytes")
    return key


def _pkcs7_unpad(value: bytes) -> bytes:
    if not value:
        raise WecomCallbackCryptoError("decrypted payload is empty")
    pad_len = value[-1]
    if pad_len < 1 or pad_len > 32:
        raise WecomCallbackCryptoError("invalid PKCS7 padding")
    padding = value[-pad_len:]
    if padding != bytes([pad_len]) * pad_len:
        raise WecomCallbackCryptoError("invalid PKCS7 padding bytes")
    return value[:-pad_len]


def decrypt_wecom_payload(
    *,
    encrypted_text: str,
    encoding_aes_key: str,
    expected_receiver_id: str = "",
) -> WecomDecryptResult:
    key = _decode_encoding_aes_key(encoding_aes_key)
    try:
        encrypted_bytes = base64.b64decode(encrypted_text.strip(), validate=True)
    except Exception as exc:  # noqa: BLE001 - normalize third-party/base64 errors.
        raise WecomCallbackCryptoError("encrypted payload is not valid base64") from exc
    if len(encrypted_bytes) == 0 or len(encrypted_bytes) % AES.block_size != 0:
        raise WecomCallbackCryptoError("encrypted payload length is invalid")

    cipher = AES.new(key, AES.MODE_CBC, key[:16])
    decrypted = _pkcs7_unpad(cipher.decrypt(encrypted_bytes))
    if len(decrypted) < 20:
        raise WecomCallbackCryptoError("decrypted payload is too short")
    message_length = struct.unpack(">I", decrypted[16:20])[0]
    message_start = 20
    message_end = message_start + message_length
    if message_end > len(decrypted):
        raise WecomCallbackCryptoError("decrypted message length is invalid")
    try:
        plaintext = decrypted[message_start:message_end].decode("utf-8")
        receiver_id = decrypted[message_end:].decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WecomCallbackCryptoError("decrypted payload is not valid utf-8") from exc
    if expected_receiver_id and receiver_id != expected_receiver_id:
        raise WecomCallbackCryptoError("decrypted receiver id does not match expected receiver")
    return WecomDecryptResult(plaintext=plaintext, receiver_id=receiver_id)


def parse_wecom_xml(xml_text: str) -> dict[str, str]:
    try:
        root = ET.fromstring(xml_text.encode("utf-8"))
    except ET.ParseError as exc:
        raise WecomCallbackCryptoError("xml payload is invalid") from exc
    if root.tag != "xml":
        raise WecomCallbackCryptoError("xml payload root must be xml")
    parsed: dict[str, str] = {}
    for child in root:
        parsed[child.tag] = child.text or ""
    return parsed


def extract_wecom_encrypt_from_xml(xml_text: str) -> str:
    parsed = parse_wecom_xml(xml_text)
    encrypt = parsed.get("Encrypt", "").strip()
    if not encrypt:
        raise WecomCallbackCryptoError("xml payload does not contain Encrypt")
    return encrypt
