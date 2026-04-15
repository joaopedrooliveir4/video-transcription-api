from sqlalchemy.orm import Session
from sqlalchemy import text

from app.models.job import Job


def fetch_next_pending_job(db: Session) -> Job | None:
    """
    Busca o próximo job com status 'pending' e trava com SELECT FOR UPDATE SKIP LOCKED.
    Garante que dois workers nunca processem o mesmo job ao mesmo tempo.
    """
    result = db.execute(
        text(
            "SELECT id FROM job "
            "WHERE status = 'pending' "
            "ORDER BY created_at ASC "
            "LIMIT 1 "
            "FOR UPDATE SKIP LOCKED"
        )
    ).fetchone()

    if result is None:
        return None

    job = db.get(Job, result[0])
    return job
