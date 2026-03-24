import os
from typing import List

from src.llm.openai_provider import OpenAIProvider
from src.llm.gemini_provider import GeminiProvider
from src.llm.grok_provider import GrokProvider
from src.llm.openrouter_provider import OpenRouterProvider
from src.utils.logger import get_logger

logger = get_logger("provider-factory")


def _is_usable_key(value: str | None) -> bool:

    if not value:
        return False

    normalized = value.strip().lower()

    return normalized not in {
        "",
        "xxxxxxxx",
        "your_key_here",
        "replace_me",
        "sk-xxxxxxxx",
    }


def get_available_providers() -> List[str]:

    available = []

    if _is_usable_key(os.getenv("OPENAI_API_KEY")):
        available.append("openai")

    if _is_usable_key(os.getenv("OPENROUTER_API_KEY")):
        available.append("openrouter")

    if _is_usable_key(os.getenv("GEMINI_API_KEY")):
        available.append("gemini")

    if _is_usable_key(os.getenv("GROK_API_KEY")):
        available.append("grok")

    return available


def get_llm_provider(provider_name: str | None = None, model_name: str | None = None):

    configured_provider = provider_name or os.getenv("LLM_PROVIDER")

    if configured_provider:
        provider = configured_provider.lower()
    elif _is_usable_key(os.getenv("OPENROUTER_API_KEY")):
        provider = "openrouter"
    elif _is_usable_key(os.getenv("OPENAI_API_KEY")):
        provider = "openai"
    elif _is_usable_key(os.getenv("GEMINI_API_KEY")):
        provider = "gemini"
    elif _is_usable_key(os.getenv("GROK_API_KEY")):
        provider = "grok"
    else:
        provider = "openai"

    logger.info(
        f"Selected LLM provider: {provider}"
        + (f" | model override: {model_name}" if model_name else "")
    )

    available = get_available_providers()

    if provider not in available and available:
        raise RuntimeError(
            f"Provider '{provider}' is not configured. Available providers: {', '.join(available)}"
        )

    if provider == "openai":
        return OpenAIProvider(model_name=model_name)

    if provider == "gemini":
        return GeminiProvider(model_name=model_name)

    if provider == "grok":
        return GrokProvider(model_name=model_name)

    if provider == "openrouter":
        return OpenRouterProvider(model_name=model_name)

    raise ValueError(f"Unsupported LLM provider: {provider}")
