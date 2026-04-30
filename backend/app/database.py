from pathlib import Path

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import DeclarativeBase, sessionmaker


DATABASE_PATH = Path(__file__).resolve().parents[1] / "pagestruct_ai.db"
DATABASE_URL = f"sqlite:///{DATABASE_PATH}"


engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def ensure_database_schema() -> None:
    inspector = inspect(engine)
    if "parse_record" not in inspector.get_table_names():
        return

    columns = {column["name"] for column in inspector.get_columns("parse_record")}
    if "main_content" not in columns:
        with engine.begin() as connection:
            connection.execute(text("ALTER TABLE parse_record ADD COLUMN main_content TEXT"))


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
