from services.providers.provider_factory import ProviderFactory


class LLMClient:
    """
    Backward-compatible facade for the MVP architecture.

    CommitGenerationService can depend on this class, while the real provider is
    resolved by ProviderFactory from environment variables.
    """

    def __init__(self) -> None:
        self.provider_client = ProviderFactory.from_environment()

    def generate(self, prompt: str) -> str:
        return self.provider_client.generate(prompt)
