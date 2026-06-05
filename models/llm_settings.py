from pydantic import BaseModel, Field, field_validator


class LLMSettings(BaseModel):
    provider: str = Field(default="deepseek")
    api_key: str | None = None
    model: str = Field(default="deepseek-v4-flash")
    base_url: str | None = Field(default="https://api.deepseek.com")
    temperature: float = Field(default=0.2)
    timeout: int = Field(default=30)
    max_tokens: int = Field(default=1200)
    json_mode: bool = Field(default=True)

    @field_validator("provider", "model")
    @classmethod
    def required_text(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("El proveedor y el modelo LLM son obligatorios.")
        return cleaned

    @field_validator("temperature")
    @classmethod
    def validate_temperature(cls, value: float) -> float:
        if value < 0 or value > 2:
            raise ValueError("LLM_TEMPERATURE debe estar entre 0 y 2.")
        return value

    @field_validator("timeout")
    @classmethod
    def validate_timeout(cls, value: int) -> int:
        if value < 1 or value > 180:
            raise ValueError("LLM_TIMEOUT debe estar entre 1 y 180 segundos.")
        return value

    @field_validator("max_tokens")
    @classmethod
    def validate_max_tokens(cls, value: int) -> int:
        if value < 300 or value > 6000:
            raise ValueError("LLM_MAX_TOKENS debe estar entre 300 y 6000.")
        return value
