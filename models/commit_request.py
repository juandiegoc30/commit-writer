from pydantic import BaseModel, Field, field_validator


ALLOWED_STYLES = {
    "conventional",
    "simple_english",
    "simple_spanish",
    "formal_business",
    "gitmoji",
    "release_notes",
}

ALLOWED_LANGUAGES = {"english", "spanish"}

ALLOWED_CHANGE_TYPES = {
    "automatic",
    "feat",
    "fix",
    "docs",
    "style",
    "refactor",
    "test",
    "chore",
    "perf",
    "build",
    "ci",
    "revert",
}

ALLOWED_FORMALITY_LEVELS = {"direct", "technical", "formal"}
ALLOWED_ALTERNATIVE_COUNTS = {1, 3, 5}


class CommitGenerationRequest(BaseModel):
    """Validated input received from the Streamlit form."""

    change_description: str = Field(..., min_length=8, max_length=1000)
    commit_style: str
    output_language: str
    change_type: str
    scope: str | None = None
    formality_level: str
    alternatives_count: int

    @field_validator("change_description")
    @classmethod
    def clean_change_description(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Change description is required.")
        if len(value) < 8:
            raise ValueError("Description must be at least 8 characters long.")
        if len(value) > 1000:
            raise ValueError("Description cannot exceed 1000 characters.")
        return value

    @field_validator("commit_style")
    @classmethod
    def validate_commit_style(cls, value: str) -> str:
        if value not in ALLOWED_STYLES:
            raise ValueError("Selected commit style is invalid.")
        return value

    @field_validator("output_language")
    @classmethod
    def validate_output_language(cls, value: str) -> str:
        if value not in ALLOWED_LANGUAGES:
            raise ValueError("Output language must be English or Spanish.")
        return value

    @field_validator("change_type")
    @classmethod
    def validate_change_type(cls, value: str) -> str:
        if value not in ALLOWED_CHANGE_TYPES:
            raise ValueError("Selected change type is invalid.")
        return value

    @field_validator("scope")
    @classmethod
    def validate_scope(cls, value: str | None) -> str | None:
        if value is None:
            return None

        cleaned = value.strip()
        if not cleaned:
            return None

        if any(character.isspace() for character in cleaned):
            raise ValueError("Scope cannot contain spaces. Use hyphens, for example: language-selector.")

        if len(cleaned) > 60:
            raise ValueError("Scope cannot exceed 60 characters.")

        return cleaned

    @field_validator("formality_level")
    @classmethod
    def validate_formality_level(cls, value: str) -> str:
        if value not in ALLOWED_FORMALITY_LEVELS:
            raise ValueError("Selected formality level is invalid.")
        return value

    @field_validator("alternatives_count")
    @classmethod
    def validate_alternatives_count(cls, value: int) -> int:
        if value not in ALLOWED_ALTERNATIVE_COUNTS:
            raise ValueError("Number of alternatives can only be 1, 3, or 5.")
        return value
