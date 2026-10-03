from sqlmodel import create_engine, SQLModel
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str
    email_host: str
    email_port: int
    email_username: str
    email_password: str

    class Config:
        env_file = ".env"


settings = Settings()

engine = create_engine(
    settings.database_url,
    echo=True,
)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)