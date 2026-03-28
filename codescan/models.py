"""Compatibility model layer backed by LangChain providers."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List

from .ai.providers import create_chat_model
from .config import config


class ModelHandler(ABC):
    """Compatibility handler used by existing GUI and helper code."""

    @abstractmethod
    def analyze_code(self, prompt: str) -> str:
        """Analyze content and return raw text."""

    @abstractmethod
    def summarize_project(self, prompt: str) -> str:
        """Summarize content and return raw text."""


class LangChainModelHandler(ModelHandler):
    """Thin wrapper around a LangChain chat model."""

    def __init__(self, model_name: str = "default"):
        self.model_name = model_name
        self.model_config = config.get_model_config(model_name)
        self.chat_model = create_chat_model(self.model_config)

    def _invoke(self, prompt: str) -> str:
        response = self.chat_model.invoke(prompt)
        content = getattr(response, "content", response)
        if isinstance(content, list):
            return "".join(str(part) for part in content)
        return str(content)

    def analyze_code(self, prompt: str) -> str:
        return self._invoke(prompt)

    def summarize_project(self, prompt: str) -> str:
        return self._invoke(prompt)


def get_model_handler(model_name: str = "default") -> ModelHandler:
    """Return a compatibility handler for the configured model."""

    model_config = config.get_model_config(model_name)
    provider = model_config.get("provider", "")
    if not provider:
        raise ValueError(f"无效的模型配置: {model_name}")
    return LangChainModelHandler(model_name=model_name)


def list_available_models() -> List[str]:
    """List available supported model configurations."""

    models = config.config.get("models", {})
    supported_models = []
    for name, model_config in models.items():
        provider = model_config.get("provider", "")
        if provider in ["openai", "anthropic", "deepseek", "custom"]:
            supported_models.append(name)
    return supported_models
