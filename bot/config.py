from pydantic_settings import BaseSettings

from bot.constants import LogLevelEnum


class Settings(BaseSettings):
    """
    Provide a pydantic ``BaseSettings`` model for the application settings.
    """

    DEPLOY_ENV: str = "LOCAL"

    LOG_LEVEL: LogLevelEnum = LogLevelEnum.DEBUG

    DISCORD_TOKEN: str
    OPENAI_API_KEY: str

    class Config:
        env_file = ".env"


settings = Settings()
