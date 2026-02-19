from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from typing import Optional, ClassVar


class Settings(BaseSettings):
    HF_TOKEN: str = Field(..., description= "Hugging face token")
    WEBHOOK_SECRET: str= Field(..., description="Webhook Secret (required for production)")
    HF_MODEL: str= Field(..., description="Model for the agent")
    HF_PROVIDER : str = Optional(..., description= "")


    model_config: ClassVar[SettingsConfigDict] = SettingsConfigDict(
        env_file=[".env"],
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

settings = Settings()