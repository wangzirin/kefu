import importlib.util
import json
from pathlib import Path


SCRIPT_PATH = Path(__file__).resolve().parents[2] / "scripts" / "evaluate_bailian_chat_quality.py"


def _load_eval_script():
    spec = importlib.util.spec_from_file_location("evaluate_bailian_chat_quality", SCRIPT_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_bailian_chat_quality_eval_blocks_without_explicit_allow(monkeypatch) -> None:
    monkeypatch.setenv("BAILIAN_API_KEY", "test-key-not-real")
    monkeypatch.setenv("BAILIAN_STANDARD_MODEL", "qwen-plus")

    def fail_urlopen(*_args, **_kwargs):
        raise AssertionError("quality eval must not call provider without allow_external_call")

    monkeypatch.setattr("app.services.model_gateway.urlopen", fail_urlopen)
    script = _load_eval_script()

    result = script.run_bailian_chat_quality_evaluation(
        allow_external_call=False,
        limit=3,
    )

    assert result["status"] == "blocked_external_call_not_allowed"
    assert result["provider_call_performed"] is False
    assert result["raw_text_logged"] is False
    assert result["summary"]["planned_cases"] == 3
    dumped = json.dumps(result, ensure_ascii=False)
    assert "test-key-not-real" not in dumped
    assert "公开测试问题" not in dumped
    assert "客户说" not in dumped


def test_bailian_chat_quality_eval_blocks_when_api_key_missing(monkeypatch) -> None:
    monkeypatch.delenv("BAILIAN_API_KEY", raising=False)
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)

    def fail_urlopen(*_args, **_kwargs):
        raise AssertionError("quality eval must not call provider without API key")

    monkeypatch.setattr("app.services.model_gateway.urlopen", fail_urlopen)
    script = _load_eval_script()

    result = script.run_bailian_chat_quality_evaluation(
        allow_external_call=True,
        limit=2,
    )

    assert result["status"] == "blocked_missing_api_key"
    assert result["provider_call_performed"] is False
    assert result["raw_text_logged"] is False
    assert result["summary"]["planned_cases"] == 2
    assert result["summary"]["attempted_calls"] == 0


def test_bailian_chat_quality_eval_calls_limited_fake_provider_and_scores_terms(monkeypatch) -> None:
    monkeypatch.setenv("BAILIAN_API_BASE", "https://provider.example/compatible-mode/v1")
    monkeypatch.setenv("BAILIAN_API_KEY", "test-key-not-real")
    monkeypatch.setenv("BAILIAN_STANDARD_MODEL", "qwen-plus")
    monkeypatch.setenv("BAILIAN_FAST_MODEL", "qwen-turbo")
    monkeypatch.setenv("BAILIAN_PREMIUM_MODEL", "qwen-max")

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
                                "content": (
                                    "您好，当前回答会依据已审核知识处理。低置信或高风险问题会进入人工审核，"
                                    "发货时间和退换货规则也应以知识库为准，不会承诺未核实政策。"
                                )
                            }
                        }
                    ],
                    "usage": {
                        "prompt_tokens": 120,
                        "completion_tokens": 38,
                        "total_tokens": 158,
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
    script = _load_eval_script()

    result = script.run_bailian_chat_quality_evaluation(
        allow_external_call=True,
        limit=2,
    )

    assert len(calls) == 2
    assert calls[0]["url"] == "https://provider.example/compatible-mode/v1/chat/completions"
    assert calls[0]["authorization"] == "Bearer test-key-not-real"
    assert result["status"] == "completed"
    assert result["provider_call_performed"] is True
    assert result["raw_text_logged"] is False
    assert result["summary"]["planned_cases"] == 2
    assert result["summary"]["attempted_calls"] == 2
    assert result["summary"]["succeeded"] == 2
    assert result["summary"]["total_tokens_or_chars"] == 316
    assert result["summary"]["forbidden_term_hits"] == 0
    assert result["summary"]["missing_expected_terms"] == 0
    assert result["cases"][0]["case_id"].startswith("p2_21_")
    assert "input_text_hash" in result["cases"][0]
    dumped = json.dumps(result, ensure_ascii=False)
    assert "test-key-not-real" not in dumped
    assert "客户说" not in dumped
    assert "公开测试问题" not in dumped


def test_bailian_chat_quality_eval_ignores_forbidden_terms_in_safe_negation() -> None:
    script = _load_eval_script()

    hits = script._score_forbidden_terms(  # noqa: SLF001 - script helper is part of the CLI contract.
        "您好，客服不能承诺最低价，也不会使用个人号外挂。",
        ("承诺最低价", "个人号外挂"),
    )

    assert hits == []
