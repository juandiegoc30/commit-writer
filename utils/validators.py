from pydantic import ValidationError

from models.commit_request import CommitGenerationRequest


def validate_generation_input(
    change_description: str,
    commit_style: str,
    output_language: str,
    change_type: str,
    scope: str | None,
    formality_level: str,
    alternatives_count: int,
) -> CommitGenerationRequest:
    try:
        return CommitGenerationRequest(
            change_description=change_description,
            commit_style=commit_style,
            output_language=output_language,
            change_type=change_type,
            scope=scope,
            formality_level=formality_level,
            alternatives_count=alternatives_count,
        )
    except ValidationError as error:
        first_error = error.errors()[0]
        message = first_error.get("msg", "Invalid input.")
        if message.startswith("Value error, "):
            message = message.replace("Value error, ", "", 1)
        raise ValueError(message) from error
