from sqlalchemy import create_engine
from config import settings
from sqlalchemy.orm import DeclarativeBase, sessionmaker

DB_URL = settings.database_url

engine = create_engine(DB_URL, echo=True)
SessionLocal = sessionmaker(autoflush=False, bind=engine, autocommit=False)

class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
