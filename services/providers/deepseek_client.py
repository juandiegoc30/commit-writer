from services.providers.openai_compatible_client import OpenAICompatibleClient


class DeepSeekClient(OpenAICompatibleClient):
    """DeepSeek adapter. DeepSeek exposes an OpenAI-compatible API."""

    def __init__(
        self,
        api_key: str,
        model: str = "deepseek-v4-flash",
        base_url: str = "https://api.deepseek.com",
        temperature: float = 0.2,
        timeout: int = 30,
        max_tokens: int = 1200,
        json_mode: bool = True,
    ) -> None:
        super().__init__(
            api_key=api_key,
            model=model,
            base_url=base_url,
            temperature=temperature,
            timeout=timeout,
            max_tokens=max_tokens,
            json_mode=json_mode,
        )
