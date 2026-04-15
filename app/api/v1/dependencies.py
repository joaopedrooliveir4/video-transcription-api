from sqlalchemy.orm import Session
from fastapi import Depends

from app.core.database import SessionLocal
from app.repositories.job_repository import JobRepository


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_repository(db: Session = Depends(get_db)) -> JobRepository:
    return JobRepository(db)
