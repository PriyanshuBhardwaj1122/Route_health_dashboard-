"""SQLAlchemy engine and session setup for SQLite."""

import os
import shutil
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# On Vercel (serverless), the filesystem is read-only except /tmp.
# We bundle a pre-seeded data.db and copy it to /tmp on cold start.
VERCEL = os.getenv("VERCEL")
if VERCEL:
    TMP_DB = "/tmp/data.db"
    BUNDLED_DB = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data.db")
    if not os.path.exists(TMP_DB) and os.path.exists(BUNDLED_DB):
        shutil.copy2(BUNDLED_DB, TMP_DB)
    DATABASE_URL = f"sqlite:///{TMP_DB}"
else:
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///data.db")

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """FastAPI dependency that yields a DB session and closes it after use."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()