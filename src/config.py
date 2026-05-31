from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    TESTING: bool
    DATABASE_URL: str
    JWT_SECRET: str
    JWT_ALGORITHM: str
    ACCESS_TOKEN_EXPIRY: int
    REFRESH_TOKEN_EXPIRY: int
    REDIS_HOST: str
    REDIS_PORT: int
    JTI_EXPIRY: int   

    model_config = SettingsConfigDict(
        env_file= ".env",
        extra="ignore"
    )

Config = Settings()