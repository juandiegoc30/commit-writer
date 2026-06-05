from pydantic import ValidationError

from models.commit_request import CommitGenerationRequest
from models.commit_result import CommitResult
from prompts.commit_prompt import build_commit_prompt
from services.llm_client import LLMClient
from utils.json_parser import JSONParseError, extract_json_object


class CommitGenerationService:
    """Coordinates validation, prompt creation, LLM execution and response parsing."""

    def __init__(self, llm_client: LLMClient | None = None) -> None:
        self.llm_client = llm_client or LLMClient()

    def generate(self, request: CommitGenerationRequest) -> CommitResult:
        prompt = build_commit_prompt(request)
        raw_response = self.llm_client.generate(prompt)

        try:
            payload = extract_json_object(raw_response)
            return CommitResult.model_validate(payload)
        except JSONParseError as error:
            raise ValueError(f"La respuesta del LLM no es JSON válido: {error}") from error
        except ValidationError as error:
            first_error = error.errors()[0]
            message = first_error.get("msg", "La respuesta del LLM no cumple la estructura esperada.")
            if message.startswith("Value error, "):
                message = message.replace("Value error, ", "", 1)
            raise ValueError(f"Respuesta inválida del LLM: {message}") from error
