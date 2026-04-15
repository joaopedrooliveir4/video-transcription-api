from uuid import UUID

from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse

from app.repositories.job_repository import JobRepository
from app.api.v1.dependencies import get_repository
from app.api.v1.transcription_service import TranscriptionService
from app.schemas.transcription import (
    TranscriptionRequest,
    TranscriptionResponse,
    TranscriptionDetailResponse,
    TranscriptionListResponse,
    JobStatusResponse,
)

router = APIRouter(prefix="/transcriptions", tags=["Transcriptions"])


@router.post("/", status_code=201)
def create_transcription(
    request: TranscriptionRequest,
    repository: JobRepository = Depends(get_repository),
):
    """
    Envia um vídeo para transcrição.
    Apenas source_url OU file_path — nunca os dois.
    """
    service = TranscriptionService(repository)
    result = service.create_transcription(request)

    # Se for duplicata, retorna 200 com a transcrição existente
    if isinstance(result, TranscriptionDetailResponse):
        return JSONResponse(
            status_code=200,
            content=result.model_dump(mode="json"),
        )

    # Job novo criado, retorna 201
    return result


@router.get("/{job_id}", response_model=JobStatusResponse)
def get_job_status(
    job_id: UUID,
    repository: JobRepository = Depends(get_repository),
):
    """
    Acompanha o status de um job via polling.
    Retorna status atual + logs + conteúdo da transcrição (se completo).
    """
    service = TranscriptionService(repository)
    return service.get_job_status(job_id)


@router.get("/", response_model=TranscriptionListResponse)
def get_transcription_history(
    page: int = Query(default=1, ge=1, description="Número da página"),
    page_size: int = Query(default=10, ge=1, le=100, description="Itens por página"),
    repository: JobRepository = Depends(get_repository),
):
    """
    Histórico paginado de transcrições.
    """
    service = TranscriptionService(repository)
    return service.get_transcription_history(page, page_size)
