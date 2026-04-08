"""
EpiChat Database Setup
SQLite engine, session factory, and base ORM class.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from pathlib import Path

# DB file lives at backend/epichat.db
DB_PATH = Path(__file__).resolve().parent.parent / "epichat.db"
DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}  # Required for SQLite + FastAPI
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """FastAPI dependency: yields a DB session and closes it after use."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Create all tables if they don't exist yet."""
    from app.db_models import User, Scan  # noqa: F401 - import needed for Base metadata
    Base.metadata.create_all(bind=engine)
    print(f"✅ EpiChat database initialized at: {DB_PATH}")
