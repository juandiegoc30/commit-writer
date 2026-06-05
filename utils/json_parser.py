import json
import re
from typing import Any


class JSONParseError(ValueError):
    """Raised when an LLM response cannot be converted into valid JSON."""


def extract_json_object(raw_response: str) -> dict[str, Any]:
    if not raw_response or not raw_response.strip():
        raise JSONParseError("La respuesta del LLM está vacía.")

    text = raw_response.strip()

    # Some providers may still wrap JSON in markdown. We remove code fences defensively.
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.IGNORECASE)
        text = re.sub(r"\s*```$", "", text)
        text = text.strip()

    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}")
        if start == -1 or end == -1 or end <= start:
            raise JSONParseError("No fue posible encontrar un objeto JSON válido en la respuesta del LLM.")

        candidate = text[start : end + 1]
        try:
            data = json.loads(candidate)
        except json.JSONDecodeError as error:
            raise JSONParseError(f"JSON mal formado: {error.msg}.") from error

    if not isinstance(data, dict):
        raise JSONParseError("La respuesta JSON debe ser un objeto, no una lista ni un valor simple.")

    return data
