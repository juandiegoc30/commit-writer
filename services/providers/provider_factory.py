import os

from dotenv import load_dotenv

from models.llm_settings import LLMSettings
from services.providers.base import BaseLLMClient
from services.providers.deepseek_client import DeepSeekClient
from services.providers.openai_compatible_client import OpenAICompatibleClient


OPENAI_COMPATIBLE_PROVIDERS = {
    "openai",
    "openrouter",
    "together",
    "groq",
    "custom_openai_compatible",
}


class ProviderFactory:
    """Creates the configured LLM client without exposing provider details to the app."""

    @staticmethod
    def from_environment() -> BaseLLMClient:
        load_dotenv()

        provider = os.getenv("LLM_PROVIDER", "deepseek").strip().lower()
        api_key = os.getenv("LLM_API_KEY")
        model = os.getenv("LLM_MODEL", "deepseek-v4-flash")
        base_url = os.getenv("LLM_BASE_URL", "https://api.deepseek.com")
        temperature = float(os.getenv("LLM_TEMPERATURE", "0.2"))
        timeout = int(os.getenv("LLM_TIMEOUT", "30"))
        max_tokens = int(os.getenv("LLM_MAX_TOKENS", "1200"))
        json_mode = os.getenv("LLM_JSON_MODE", "true").strip().lower() == "true"

        settings = LLMSettings(
            provider=provider,
            api_key=api_key,
            model=model,
            base_url=base_url,
            temperature=temperature,
            timeout=timeout,
            max_tokens=max_tokens,
            json_mode=json_mode,
        )

        if not settings.api_key:
            raise ValueError("Falta LLM_API_KEY. Crea un archivo .env a partir de .env.example y agrega tu API key.")

        if settings.provider == "deepseek":
            return DeepSeekClient(
                api_key=settings.api_key,
                model=settings.model,
                base_url=settings.base_url or "https://api.deepseek.com",
                temperature=settings.temperature,
                timeout=settings.timeout,
                max_tokens=settings.max_tokens,
                json_mode=settings.json_mode,
            )

        if settings.provider in OPENAI_COMPATIBLE_PROVIDERS:
            return OpenAICompatibleClient(
                api_key=settings.api_key,
                model=settings.model,
                base_url=settings.base_url,
                temperature=settings.temperature,
                timeout=settings.timeout,
                max_tokens=settings.max_tokens,
                json_mode=settings.json_mode,
            )

        raise ValueError(
            f"Proveedor LLM no soportado: {settings.provider}. "
            "Usa deepseek, openai, openrouter, together, groq o custom_openai_compatible."
        )
