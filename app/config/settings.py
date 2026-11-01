from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")
    app_base_url: str = "http://127.0.0.1:8000"
    frontend_base_url: str = "http://localhost:5173"

    db_echo: bool = False
    paystack_secret_key: str = ""
    upload_dir: str = "uploads"
    cors_origins: str = ""  # extra allowed origins, comma separated
    max_image_bytes: int = 5 * 1024 * 1024
    database_url: str
    email_host: str
    email_port: int

    email_username: str
    email_password: str
    mailjet_api_key: str
    mailjet_secret_key: str

    secret_key: str
    algorithm: str = "HS256"
    verification_token_expire_minutes: int = 10
    password_reset_token_expire_minutes: int = 10
    access_token_expire_minutes: int = 30

    admin_first_name: str
    admin_last_name: str
    admin_email: str
    admin_password: str


settings = Settings()