import logging
import time
import signal
import sys
import os
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

import httpx

from app.core.config import settings
from app.core.database import SessionLocal
from app.worker.queue import fetch_next_pending_job
from app.models.job import Job, JobLog, Transcription
from app.modules.validation.media_type import is_valid_video
from app.modules.validation.metadata import get_video_metadata
from app.modules.validation.url_validator import is_valid_video_url
from app.modules.ingestion.hasher import generate_hash
from app.modules.ingestion.storage import save_temp_file, remove_temp_file
from app.modules.transcription.transcriber import transcribe_video
from app.modules.storage.backup import save_as_txt, save_as_json
from app.repositories.job_repository import JobRepository

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("worker")

# Flag para shutdown gracioso
shutdown_requested = False


def signal_handler(signum, frame):
    global shutdown_requested
    logger.info("Shutdown solicitado. Finalizando jobs em andamento...")
    shutdown_requested = True


signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)


def add_log(repository: JobRepository, job: Job, message: str, status: str):
    """Registra um log para o job."""
    log = JobLog(
        job_id=job.id,
        message=message,
        status=status,
    )
    repository.create_log(log)
    logger.info(f"[Job {job.id}] {message} -> {status}")


def download_video_from_url(url: str) -> bytes:
    """Baixa o vídeo de uma URL remota."""
    with httpx.Client(timeout=settings.worker_timeout) as client:
        response = client.get(url)
        response.raise_for_status()
        return response.content


def process_job(job: Job):
    """Processa um job individual de transcrição."""
    db = SessionLocal()
    repository = JobRepository(db)

    try:
        # 1. Marcar como processing
        job.status = "processing"
        job.started_at = datetime.now()
        db.commit()
        add_log(repository, job, "Iniciando processamento do job", "ok")

        file_path = None

        # 2. Ingestão — obter o arquivo de vídeo
        if job.source_url:
            add_log(repository, job, "Validando URL do vídeo", "ok")

            if not is_valid_video_url(job.source_url):
                add_log(repository, job, "URL não contém um vídeo válido", "error")
                raise Exception("URL não contém um vídeo válido")

            add_log(repository, job, "Baixando vídeo da URL", "ok")
            video_data = download_video_from_url(job.source_url)
            file_path = save_temp_file(video_data)
            add_log(repository, job, "Download do vídeo concluído", "ok")

        elif job.file_path:
            file_path = job.file_path
            add_log(repository, job, "Arquivo local identificado", "ok")

        # 3. Validação — integridade do arquivo
        add_log(repository, job, "Validando integridade do vídeo", "ok")

        if not is_valid_video(file_path):
            add_log(repository, job, "Arquivo não é um vídeo válido (magic bytes)", "error")
            raise Exception("Arquivo não é um vídeo válido")

        add_log(repository, job, "Integridade do vídeo validada", "ok")

        # 4. Validação — metadados (duração + áudio)
        add_log(repository, job, "Validando metadados do vídeo", "ok")
        metadata = get_video_metadata(file_path)

        if not metadata.get("has_audio"):
            add_log(repository, job, "Vídeo não possui faixa de áudio", "error")
            raise Exception("Vídeo não possui faixa de áudio para transcrição")

        duration = metadata.get("duration", 0)
        add_log(repository, job, f"Duração do vídeo: {duration:.1f}s", "ok")
        add_log(repository, job, "Metadados do vídeo validados", "ok")

        # 5. Deduplicação via hash
        add_log(repository, job, "Calculando hash do conteúdo", "ok")
        file_hash = generate_hash(file_path)

        existing_transcription = repository.get_transcription_by_hash(file_hash)
        if existing_transcription:
            add_log(repository, job, "Transcrição já existe — retornando resultado existente", "ok")
            job.transcription_id = existing_transcription.id
            job.status = "completed"
            job.finished_at = datetime.now()
            db.commit()

            # Limpa arquivo temporário se foi baixado
            if job.source_url and file_path:
                remove_temp_file(file_path)

            return

        # 6. Transcrição com Whisper
        add_log(repository, job, "Iniciando transcrição do vídeo", "ok")
        transcription_text = transcribe_video(file_path)
        add_log(repository, job, "Transcrição concluída com sucesso", "ok")

        # 7. Persistência — salvar transcrição no banco
        transcription = Transcription(
            hash=file_hash,
            content=transcription_text,
        )
        created_transcription = repository.create_transcription(transcription)

        # 8. Backup em arquivo
        add_log(repository, job, "Salvando backup da transcrição", "ok")
        save_as_txt(job.id, transcription_text)
        save_as_json(job.id, transcription_text)

        # 9. Finalizar job
        job.transcription_id = created_transcription.id
        job.status = "completed"
        job.finished_at = datetime.now()
        db.commit()
        add_log(repository, job, "Job finalizado com sucesso", "ok")

        # 10. Limpar arquivo temporário
        if job.source_url and file_path:
            remove_temp_file(file_path)
            add_log(repository, job, "Arquivo temporário removido", "ok")

    except Exception as e:
        db.rollback()
        logger.error(f"[Job {job.id}] Erro: {e}")

        # Reabrir sessão limpa para atualizar retry
        db = SessionLocal()
        repository = JobRepository(db)
        job = repository.get_job_by_id(job.id)

        job.retry_count += 1

        if job.retry_count >= settings.max_retries:
            job.status = "error"
            job.finished_at = datetime.now()
            add_log(repository, job, f"Falha definitiva após {job.retry_count} tentativas: {str(e)}", "error")
        else:
            job.status = "pending"
            add_log(repository, job, f"Tentativa {job.retry_count}/{settings.max_retries} falhou: {str(e)}. Retornando à fila.", "error")

        db.commit()

    finally:
        db.close()


def run_worker():
    """Loop principal do worker — faz polling no banco buscando jobs pendentes."""
    logger.info("Worker iniciado.")
    logger.info(f"  MAX_CONCURRENT_JOBS: {settings.max_concurrent_jobs}")
    logger.info(f"  MAX_RETRIES: {settings.max_retries}")
    logger.info(f"  WORKER_TIMEOUT: {settings.worker_timeout}s")
    logger.info(f"  POLLING_INTERVAL: {settings.polling_interval}s")

    executor = ThreadPoolExecutor(max_workers=settings.max_concurrent_jobs)

    while not shutdown_requested:
        db = SessionLocal()
        try:
            job = fetch_next_pending_job(db)

            if job:
                logger.info(f"Job encontrado: {job.id}")
                # Submete para execução no pool de threads
                executor.submit(process_job, job)
            else:
                logger.debug("Nenhum job pendente. Aguardando...")

        except Exception as e:
            logger.error(f"Erro no polling: {e}")
        finally:
            db.close()

        time.sleep(settings.polling_interval)

    # Aguarda jobs em andamento finalizarem
    logger.info("Aguardando jobs em andamento finalizarem...")
    executor.shutdown(wait=True)
    logger.info("Worker encerrado.")
