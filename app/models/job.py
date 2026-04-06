from datetime import datetime
from app.core.database import Base
import uuid
from sqlalchemy import Uuid, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from typing import Optional

class Transcription(Base):
    __tablename__ = "transcription"
    id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=uuid.uuid4
    )
    hash: Mapped[str] = mapped_column(unique=True)
    content: Mapped[str] = mapped_column()
    created_at: Mapped[datetime] = mapped_column(default=datetime.now)


class Job(Base):
    __tablename__ = "job"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4
    )
    transcription_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("transcription.id"), nullable=True
    )
    status: Mapped[str] = mapped_column(default="pending")
    source_url: Mapped[Optional[str]] = mapped_column(nullable=True)
    file_path: Mapped[Optional[str]] = mapped_column(nullable=True)
    retry_count: Mapped[int] = mapped_column(default=0)
    created_at: Mapped[datetime] = mapped_column(default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.now)
    started_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    finished_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)

class JobLog(Base):
    __tablename__ = "job_log"
    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4
    )
    job_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("job.id")
    )
    message: Mapped[str] = mapped_column()
    status: Mapped[str] = mapped_column()
    created_at: Mapped[datetime] = mapped_column(default=datetime.now)