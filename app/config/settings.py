from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")
    app_base_url: str = "http://127.0.0.1:8000"
    verification_token_expire_hours: int = 24
    db_echo: bool = False
    secret_key: str
    paystack_secret_key: str = ""
    database_url: str
    email_host: str
    email_port: int
    email_username: str
    email_password: str

    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30


settings = Settings()