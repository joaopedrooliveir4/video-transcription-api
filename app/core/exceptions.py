from fastapi import Request
from fastapi.responses import JSONResponse


class JobNotFoundError(Exception):
    """Job não encontrado no banco de dados."""
    def __init__(self, job_id: str):
        self.job_id = job_id
        self.message = f"Job '{job_id}' não encontrado."
        super().__init__(self.message)


class VideoValidationError(Exception):
    """Erro durante a validação do vídeo."""
    def __init__(self, detail: str):
        self.detail = detail
        super().__init__(self.detail)


class DownloadError(Exception):
    """Erro ao baixar vídeo de URL remota."""
    def __init__(self, url: str, detail: str = ""):
        self.url = url
        self.detail = detail or f"Falha ao baixar vídeo de: {url}"
        super().__init__(self.detail)


class TranscriptionError(Exception):
    """Erro durante o processo de transcrição."""
    def __init__(self, detail: str):
        self.detail = detail
        super().__init__(self.detail)


# --- Exception Handlers para registrar no FastAPI ---

async def job_not_found_handler(request: Request, exc: JobNotFoundError):
    return JSONResponse(
        status_code=404,
        content={"detail": exc.message}
    )


async def video_validation_handler(request: Request, exc: VideoValidationError):
    return JSONResponse(
        status_code=422,
        content={"detail": exc.detail}
    )


async def download_error_handler(request: Request, exc: DownloadError):
    return JSONResponse(
        status_code=422,
        content={"detail": exc.detail}
    )


async def transcription_error_handler(request: Request, exc: TranscriptionError):
    return JSONResponse(
        status_code=500,
        content={"detail": exc.detail}
    )