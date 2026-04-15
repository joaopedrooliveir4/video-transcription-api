from typing import Optional, List
import uuid
from pydantic import BaseModel, ConfigDict, model_validator
import datetime

class TranscriptionRequest(BaseModel):
    source_url: Optional[str] = None
    file_path: Optional[str] = None

    @model_validator(mode='after')
    def validate_input(self):
        if self.source_url and self.file_path:
            raise ValueError("Envie apenas source_url ou file_path, não ambos.")
        if not self.source_url and not self.file_path:
            raise ValueError("Envie source_url ou file_path. Pelo menos um é obrigatório.")
        return self

class TranscriptionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    status: str

class JobLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    message: str
    status: str
    created_at: datetime.datetime

class JobStatusResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    status: str
    transcription_content: Optional[str] = None
    logs: List[JobLogResponse]

class TranscriptionDetailResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    content: str
    created_at: datetime.datetime

class TranscriptionListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    status: str
    created_at: datetime.datetime

class TranscriptionListResponse(BaseModel):
    page: int
    total: int
    items: List[TranscriptionListItem]