from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from app.core.config import settings

# Create engine with pool configuration suitable for production
engine = create_engine(
    settings.sqlalchemy_database_uri,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db() -> Generator:
    """
    SQLAlchemy database session dependency helper.
    Yields a db session and ensures clean closure after requests finish.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
