from services.providers.base import BaseLLMClient


class OpenAICompatibleClient(BaseLLMClient):
    """Generic adapter for OpenAI-compatible chat-completion APIs."""

    def __init__(
        self,
        api_key: str,
        model: str,
        base_url: str | None = None,
        temperature: float = 0.2,
        timeout: int = 30,
        max_tokens: int = 1200,
        json_mode: bool = True,
    ) -> None:
        if not api_key:
            raise ValueError("Falta LLM_API_KEY. Configura la clave en el archivo .env.")

        try:
            from openai import OpenAI
        except ModuleNotFoundError as error:
            raise RuntimeError(
                "Falta la dependencia 'openai'. Ejecuta: pip install -r requirements.txt"
            ) from error

        client_kwargs = {"api_key": api_key, "timeout": timeout}
        if base_url:
            client_kwargs["base_url"] = base_url

        self.client = OpenAI(**client_kwargs)
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.json_mode = json_mode

    def generate(self, prompt: str) -> str:
        try:
            from openai import APIConnectionError, APIStatusError, APITimeoutError
        except ModuleNotFoundError as error:
            raise RuntimeError(
                "Falta la dependencia 'openai'. Ejecuta: pip install -r requirements.txt"
            ) from error

        request_payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are an expert in Git, Conventional Commits, SemVer and technical writing. "
                        "You must return strict json only."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
        }

        if self.json_mode:
            request_payload["response_format"] = {"type": "json_object"}

        try:
            response = self.client.chat.completions.create(**request_payload)
        except APITimeoutError as error:
            raise RuntimeError("Se agotó el tiempo de espera al conectar con el proveedor LLM.") from error
        except APIConnectionError as error:
            raise RuntimeError("No fue posible conectar con el proveedor LLM.") from error
        except APIStatusError as error:
            status = getattr(error, "status_code", "desconocido")
            detail = getattr(error, "message", str(error))
            raise RuntimeError(f"El proveedor LLM respondió con error HTTP {status}: {detail}") from error
        except Exception as error:
            raise RuntimeError(f"Error inesperado al llamar al proveedor LLM: {error}") from error

        content = response.choices[0].message.content
        if not content:
            raise RuntimeError("El proveedor LLM devolvió una respuesta vacía.")

        return content
