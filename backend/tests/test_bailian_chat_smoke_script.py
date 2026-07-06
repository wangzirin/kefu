import importlib.util
import json
from pathlib import Path


SCRIPT_PATH = Path(__file__).resolve().parents[2] / "scripts" / "smoke_bailian_chat_model.py"


def _load_smoke_script():
    spec = importlib.util.spec_from_file_location("smoke_bailian_chat_model", SCRIPT_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_bailian_chat_smoke_blocks_external_call_without_explicit_allow(monkeypatch) -> None:
    monkeypatch.setenv("BAILIAN_API_KEY", "test-key-not-real")
    monkeypatch.setenv("BAILIAN_STANDARD_MODEL", "qwen3.7-plus")

    def fail_urlopen(*_args, **_kwargs):
        raise AssertionError("smoke must not call provider without allow_external_call")

    monkeypatch.setattr("app.services.model_gateway.urlopen", fail_urlopen)
    script = _load_smoke_script()

    result = script.run_bailian_chat_smoke(
        allow_external_call=False,
        sample_text="公开测试问题：标准客服系统如何处理低置信问题？",
    )

    assert result["status"] == "blocked_external_call_not_allowed"
    assert result["provider_call_performed"] is False
    assert result["raw_text_logged"] is False
    assert result["provider"] == "bailian"
    assert result["model"] == "qwen3.7-plus"
    assert "test-key-not-real" not in json.dumps(result, ensure_ascii=False)
    assert "公开测试问题" not in json.dumps(result, ensure_ascii=False)


def test_bailian_chat_smoke_blocks_when_api_key_missing(monkeypatch) -> None:
    monkeypatch.delenv("BAILIAN_API_KEY", raising=False)
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)

    def fail_urlopen(*_args, **_kwargs):
        raise AssertionError("smoke must not call provider without API key")

    monkeypatch.setattr("app.services.model_gateway.urlopen", fail_urlopen)
    script = _load_smoke_script()

    result = script.run_bailian_chat_smoke(
        allow_external_call=True,
        sample_text="公开测试问题：标准客服系统如何处理低置信问题？",
    )

    assert result["status"] == "blocked_missing_api_key"
    assert result["provider_call_performed"] is False
    assert result["raw_text_logged"] is False
    assert result["provider"] == "bailian"
    assert result["route_name"] == "standard_support"


def test_bailian_chat_smoke_calls_openai_compatible_provider_when_allowed(monkeypatch) -> None:
    monkeypatch.setenv("BAILIAN_API_BASE", "https://provider.example/compatible-mode/v1")
    monkeypatch.setenv("BAILIAN_API_KEY", "test-key-not-real")
    monkeypatch.setenv("BAILIAN_STANDARD_MODEL", "qwen3.7-plus")

    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def read(self) -> bytes:
            return json.dumps(
                {
                    "choices": [
                        {
                            "message": {
                                "content": "您好，这类低置信问题会先生成草稿，并进入人工审核后再发送。"
                            }
                        }
                    ],
                    "usage": {
                        "prompt_tokens": 91,
                        "completion_tokens": 21,
                        "total_tokens": 112,
                    },
                }
            ).encode("utf-8")

    calls: list[dict] = []

    def fake_urlopen(request, timeout):
        calls.append(
            {
                "url": request.full_url,
                "timeout": timeout,
                "authorization": request.headers.get("Authorization"),
            }
        )
        return FakeResponse()

    monkeypatch.setattr("app.services.model_gateway.urlopen", fake_urlopen)
    script = _load_smoke_script()

    result = script.run_bailian_chat_smoke(
        allow_external_call=True,
        sample_text="公开测试问题：标准客服系统如何处理低置信问题？",
    )

    assert calls == [
        {
            "url": "https://provider.example/compatible-mode/v1/chat/completions",
            "timeout": 20.0,
            "authorization": "Bearer test-key-not-real",
        }
    ]
    assert result["status"] == "succeeded"
    assert result["provider"] == "bailian"
    assert result["model"] == "qwen3.7-plus"
    assert result["route_name"] == "standard_support"
    assert result["provider_call_performed"] is True
    assert result["usage_summary"]["prompt_tokens_or_chars"] == 91
    assert result["usage_summary"]["total_tokens_or_chars"] == 112
    assert result["raw_text_logged"] is False
    dumped = json.dumps(result, ensure_ascii=False)
    assert "test-key-not-real" not in dumped
    assert "公开测试问题" not in dumped
