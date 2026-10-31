from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    anthropic_api_key: SecretStr
    llm_model: str = "claude-haiku-5-5"
    llm_effort: str = "low"
    anki_connect_url: str = "http://127.0.0.1:8765"
    default_deck: str = ""
