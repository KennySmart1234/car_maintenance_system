from sqlmodel import create_engine, SQLModel
from app.config.settings import settings

engine = create_engine(settings.database_url, echo=settings.db_echo)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)