import pytest


def test_openai_compatible_provider_returns_chat_model() -> None:
    from codescan.ai.providers import create_chat_model

    model = create_chat_model(
        {
            "provider": "deepseek",
            "model": "deepseek-chat",
            "api_key": "test-key",
            "base_url": "https://api.deepseek.com",
            "max_tokens": 2048,
        }
    )

    assert model.__class__.__name__ == "ChatOpenAI"
    assert hasattr(model, "with_structured_output")


def test_anthropic_provider_fails_cleanly_without_optional_dependency(monkeypatch: pytest.MonkeyPatch) -> None:
    from codescan.ai import providers

    monkeypatch.setattr(providers, "LANGCHAIN_ANTHROPIC_AVAILABLE", False)

    with pytest.raises(RuntimeError, match="langchain-anthropic"):
        providers.create_chat_model(
            {
                "provider": "anthropic",
                "model": "claude-3-5-sonnet-latest",
                "api_key": "test-key",
            }
        )
