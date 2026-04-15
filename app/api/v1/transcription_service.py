from typing import Union
from uuid import UUID

from app.repositories.job_repository import JobRepository
from app.modules.ingestion.hasher import generate_hash
from app.models.job import Job, Transcription, JobLog
from app.core.exceptions import JobNotFoundError
from app.schemas.transcription import (
    TranscriptionRequest,
    TranscriptionResponse,
    TranscriptionDetailResponse,
    JobLogResponse,
    JobStatusResponse,
    TranscriptionListItem,
    TranscriptionListResponse,
)


class TranscriptionService:
    def __init__(self, repository: JobRepository):
        self.repository = repository

    def create_transcription(
        self, transcription_request: TranscriptionRequest
    ) -> Union[TranscriptionResponse, TranscriptionDetailResponse]:
        """
        Cria um job de transcrição.

        - Se file_path: gera hash e verifica duplicação antes de criar o job.
        - Se source_url: cria o job direto (o worker fará download + hash + deduplicação).
        """

        # Deduplicação apenas para file_path (arquivo local disponível)
        if transcription_request.file_path:
            file_hash = generate_hash(transcription_request.file_path)
            existing = self.repository.get_transcription_by_hash(file_hash)
            if existing:
                return TranscriptionDetailResponse(
                    id=existing.id,
                    content=existing.content,
                    created_at=existing.created_at,
                )

        # Cria o job com status pending
        job = Job(
            file_path=transcription_request.file_path,
            source_url=transcription_request.source_url,
        )
        created_job = self.repository.create_job(job)

        return TranscriptionResponse(
            id=created_job.id,
            status=created_job.status,
        )

    def get_job_status(self, job_id: UUID) -> JobStatusResponse:
        """Retorna o status de um job com seus logs."""
        job = self.repository.get_job_by_id(job_id)
        if not job:
            raise JobNotFoundError(str(job_id))

        result_logs = self.repository.get_logs_by_job_id(job_id)
        logs = [
            JobLogResponse(
                message=log.message,
                status=log.status,
                created_at=log.created_at,
            )
            for log in result_logs
        ]

        # Inclui conteúdo da transcrição se o job está completo
        transcription_content = None
        if job.status == "completed" and job.transcription_id:
            transcription = self.repository.get_transcription_by_id(job.transcription_id)
            if transcription:
                transcription_content = transcription.content

        return JobStatusResponse(
            id=job.id,
            status=job.status,
            transcription_content=transcription_content,
            logs=logs,
        )

    def get_transcription_history(
        self, page: int, page_size: int
    ) -> TranscriptionListResponse:
        """Retorna o histórico paginado de jobs."""
        history = self.repository.get_jobs_paginated(page, page_size)
        total = self.repository.get_total_jobs()

        items = [
            TranscriptionListItem(
                id=job.id,
                status=job.status,
                created_at=job.created_at,
            )
            for job in history
        ]

        return TranscriptionListResponse(
            page=page,
            total=total,
            items=items,
        )
