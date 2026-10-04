"""Database setup: SQLite + SQLAlchemy. Auto-creates tables on startup."""
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from backend.config import DATABASE_URL

# Resolve relative SQLite path against project root (parent of backend/)
if DATABASE_URL.startswith("sqlite:///./"):
    _project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    _db_file = DATABASE_URL.replace("sqlite:///./", "")
    _db_path = os.path.join(_project_root, _db_file)
    SQLALCHEMY_DATABASE_URL = f"sqlite:///{_db_path}"
else:
    SQLALCHEMY_DATABASE_URL = DATABASE_URL

# check_same_thread=False is required for FastAPI + background simulation thread
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """FastAPI dependency: yields a DB session, always closes it."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Create all tables. Safe to call on every startup."""
    from backend import models  # noqa: F401  (register models)
    Base.metadata.create_all(bind=engine)
