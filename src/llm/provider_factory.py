import os

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


def get_llm_provider():

    configured_provider = os.getenv("LLM_PROVIDER")

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

    logger.info(f"Selected LLM provider: {provider}")

    if provider == "openai":
        return OpenAIProvider()

    if provider == "gemini":
        return GeminiProvider()

    if provider == "grok":
        return GrokProvider()

    if provider == "openrouter":
        return OpenRouterProvider()

    raise ValueError(f"Unsupported LLM provider: {provider}")
