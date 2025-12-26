from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from uuid import UUID


class PostResponse(BaseModel):
    id: UUID
    data_id: str
    publish_time: Optional[datetime] = None
    content_type: Optional[str] = None
    post_type: Optional[str] = None
    read_7d: Optional[float] = None
    interact_7d: Optional[float] = None
    read_14d: Optional[float] = None
    interact_14d: Optional[float] = None

    class Config:
        from_attributes = True


class PostDetail(BaseModel):
    id: UUID
    dataset_id: UUID
    data_id: str
    publish_time: Optional[datetime] = None
    publish_link: Optional[str] = None
    content_type: Optional[str] = None
    post_type: Optional[str] = None
    source: Optional[str] = None
    style_info: Optional[str] = None
    
    # 7天指标
    read_7d: Optional[float] = None
    interact_7d: Optional[float] = None
    visit_7d: Optional[float] = None
    want_7d: Optional[float] = None
    
    # 14天指标
    read_14d: Optional[float] = None
    interact_14d: Optional[float] = None
    visit_14d: Optional[float] = None
    want_14d: Optional[float] = None
    
    created_at: datetime

    class Config:
        from_attributes = True
