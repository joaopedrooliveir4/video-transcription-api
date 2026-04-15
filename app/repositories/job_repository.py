from typing import List
from uuid import UUID

from app.core.database import SessionLocal
from app.models.job import Job, JobLog, Transcription

class JobRepository:
    def __init__(self, db: SessionLocal):
        self.db = db

    def create_job(self, job: Job) -> Job:
        self.db.add(job)
        self.db.commit()

        self.db.refresh(job)
        return job

    def get_job_by_id(self, id: UUID) -> Job:
        return self.db.get(Job, id)

    def get_transcription_by_hash(self, hash: str) -> Transcription:
        return self.db.query(Transcription).filter(Transcription.hash == hash).first()

    def get_transcription_by_id(self, id: UUID) -> Transcription:
        return self.db.get(Transcription, id)

    def update_job_status(self, id: UUID, status: str) -> Job:
        job = self.db.get(Job, id)
        job.status = status
        self.db.commit()
        self.db.refresh(job)

        return job

    def create_log(self, log: JobLog) -> JobLog:
        self.db.add(log)
        self.db.commit()
        self.db.refresh(log)

        return log

    def create_transcription(self, transcription: Transcription) -> Transcription:
        self.db.add(transcription)
        self.db.commit()
        self.db.refresh(transcription)
        return transcription

    def get_pending_jobs(self) -> List[Job]:
        return self.db.query(Job).filter(Job.status == "pending").all()

    def get_jobs_paginated(self, page, page_size) -> List[Job]:
        return self.db.query(Job).order_by(Job.created_at.desc()).limit(page_size).offset((page - 1) * page_size).all()

    def get_logs_by_job_id(self, job_id: UUID) -> List[JobLog]:
        return self.db.query(JobLog).filter(JobLog.job_id == job_id).order_by(JobLog.created_at.asc()).all()

    def get_total_jobs(self) -> int:
        return self.db.query(Job).count()