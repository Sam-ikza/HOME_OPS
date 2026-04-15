import logging

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker

from config import settings

logger = logging.getLogger(__name__)

Base = declarative_base()

_connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}

engine = create_engine(settings.database_url, connect_args=_connect_args, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)


def get_db():
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    # Import models here to avoid circular imports at module load time.
    from database import models  # noqa: F401

    if not settings.database_auto_create:
        logger.info("database auto-create skipped; run Alembic migrations instead")
        return

    Base.metadata.create_all(bind=engine)
    logger.info("database initialized")