"""
Database initialization and migration utilities.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.models.database import Base


def init_db():
    """Initialize database and create tables."""
    engine = create_engine(settings.DATABASE_URL, echo=settings.DATABASE_ECHO)
    Base.metadata.create_all(bind=engine)
    print("✅ Database tables created successfully")
    return engine


def get_engine():
    """Get SQLAlchemy engine."""
    return create_engine(
        settings.DATABASE_URL,
        echo=settings.DATABASE_ECHO,
        pool_size=settings.DATABASE_POOL_SIZE,
        max_overflow=settings.DATABASE_MAX_OVERFLOW,
    )


def get_session():
    """Get database session."""
    engine = get_engine()
    Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return Session()


if __name__ == "__main__":
    init_db()
