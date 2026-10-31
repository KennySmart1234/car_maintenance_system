from sqlalchemy import text
from sqlmodel import create_engine, SQLModel
from app.config.settings import settings

engine = create_engine(settings.database_url, echo=settings.db_echo)

# create_all() creates missing tables but never adds columns to tables that
# already exist, so new columns are listed here (Postgres: IF NOT EXISTS).
_ADDED_COLUMNS = [
    "ALTER TABLE maintenance_requests ADD COLUMN IF NOT EXISTS inspection_notes TEXT",
    "ALTER TABLE maintenance_requests ADD COLUMN IF NOT EXISTS inspected_at TIMESTAMP WITH TIME ZONE",
]


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

    if engine.dialect.name == "postgresql":
        with engine.begin() as connection:
            for statement in _ADDED_COLUMNS:
                connection.execute(text(statement))
