from typing import Optional, List
import uuid
from pydantic import BaseModel
import datetime

class TranscriptionRequest(BaseModel):
    source_url: Optional[str] = None
    file_path : Optional[str] = None

class TranscriptionResponse(BaseModel):
    id: uuid.UUID
    status: str

class JobLogResponse(BaseModel):
    message: str
    status: str
    created_at: datetime.datetime

class JobStatusResponse(BaseModel):
    id: uuid.UUID
    status: str
    logs: List[JobLogResponse]

class TranscriptionListItem(BaseModel):
    id: uuid.UUID
    status: str
    created_at: datetime.datetime

class TranscriptionListResponse(BaseModel):
    page: int
    total: int
    items: List[TranscriptionListItem]