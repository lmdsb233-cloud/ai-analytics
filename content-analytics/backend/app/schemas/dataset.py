from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from uuid import UUID


class DatasetCreate(BaseModel):
    name: str


class DatasetResponse(BaseModel):
    id: UUID
    name: str
    original_filename: str
    status: str
    row_count: int
    progress: Optional[str] = None
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DatasetList(BaseModel):
    items: List[DatasetResponse]
    total: int
