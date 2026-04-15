from fastapi import FastAPI

from app.api.v1.routes.transcription import router as transcription_router
from app.core.exceptions import (
    JobNotFoundError,
    VideoValidationError,
    DownloadError,
    TranscriptionError,
    job_not_found_handler,
    video_validation_handler,
    download_error_handler,
    transcription_error_handler,
)

app = FastAPI(
    title="API de Transcrição de Vídeos",
    description="API assíncrona para transcrição de vídeos via URL ou upload, com validação, histórico e deduplicação automática.",
    version="1.0.0",
)

# --- Registra Rotas ---
app.include_router(transcription_router, prefix="/api/v1")

# --- Registra Exception Handlers ---
app.add_exception_handler(JobNotFoundError, job_not_found_handler)
app.add_exception_handler(VideoValidationError, video_validation_handler)
app.add_exception_handler(DownloadError, download_error_handler)
app.add_exception_handler(TranscriptionError, transcription_error_handler)


@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "ok"}
