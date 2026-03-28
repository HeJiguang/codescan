"""LangChain model provider factory."""

from __future__ import annotations

from typing import Any, Dict

from langchain.chat_models import init_chat_model

try:
    import langchain_anthropic  # noqa: F401

    LANGCHAIN_ANTHROPIC_AVAILABLE = True
except ImportError:
    LANGCHAIN_ANTHROPIC_AVAILABLE = False


OPENAI_COMPATIBLE_PROVIDERS = {"openai", "deepseek", "custom"}


def create_chat_model(model_config: Dict[str, Any]):
    """Create a LangChain chat model from repo config."""

    provider = model_config.get("provider", "")
    model = model_config.get("model", "")
    api_key = model_config.get("api_key", "")
    max_tokens = int(model_config.get("max_tokens", 8192))
    temperature = float(model_config.get("temperature", 0.1))

    if provider in OPENAI_COMPATIBLE_PROVIDERS:
        kwargs: Dict[str, Any] = {
            "model": model,
            "model_provider": "openai",
            "api_key": api_key,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        base_url = model_config.get("base_url") or model_config.get("api_url")
        if base_url:
            kwargs["base_url"] = base_url
        extra_body = model_config.get("extra_body")
        if extra_body:
            kwargs["extra_body"] = extra_body
        return init_chat_model(**kwargs)

    if provider == "anthropic":
        if not LANGCHAIN_ANTHROPIC_AVAILABLE:
            raise RuntimeError(
                "Anthropic provider requires the optional dependency "
                "'langchain-anthropic'."
            )
        return init_chat_model(
            model=model,
            model_provider="anthropic",
            api_key=api_key,
            temperature=temperature,
            max_tokens=max_tokens,
        )

    raise ValueError(f"不支持的模型提供商: {provider}")
