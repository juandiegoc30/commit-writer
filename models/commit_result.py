from pydantic import BaseModel, Field, field_validator


class CommitResult(BaseModel):
    """Normalized and validated response returned by the LLM."""

    recommended_commit: str = Field(..., min_length=1)
    alternatives: list[str] = Field(default_factory=list)
    explanation: str = Field(..., min_length=1)
    semver_suggestion: str = Field(...)
    full_command: str = Field(..., min_length=1)
    warnings: list[str] = Field(default_factory=list)

    @field_validator("recommended_commit", "explanation", "full_command")
    @classmethod
    def strip_required_text(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("La respuesta del LLM contiene un campo obligatorio vacío.")
        return cleaned

    @field_validator("alternatives", "warnings")
    @classmethod
    def clean_string_lists(cls, values: list[str]) -> list[str]:
        return [item.strip() for item in values if isinstance(item, str) and item.strip()]

    @field_validator("semver_suggestion")
    @classmethod
    def validate_semver_suggestion(cls, value: str) -> str:
        normalized = value.strip().lower()
        if normalized not in {"patch", "minor", "major", "none"}:
            raise ValueError("La sugerencia SemVer debe ser patch, minor, major o none.")
        return normalized
