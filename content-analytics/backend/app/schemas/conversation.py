from pydantic import BaseModel
from typing import Optional, List, Dict, Literal
from uuid import UUID
from datetime import datetime


class ConversationMessageCreate(BaseModel):
    content: str


class ConversationCreate(BaseModel):
    title: Optional[str] = None
    context_type: Literal["general", "analysis", "analysis_result"] = "general"
    context_analysis_id: Optional[UUID] = None
    context_analysis_result_id: Optional[UUID] = None


class ConversationMessageResponse(BaseModel):
    id: UUID
    role: str
    content: str
    extra_data: Optional[Dict] = None  # 原metadata，因SQLAlchemy保留字改名
    tokens_used: Optional[Dict] = None
    model_name: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class ConversationResponse(BaseModel):
    id: UUID
    title: Optional[str]
    context_type: str
    context_analysis_id: Optional[UUID] = None
    context_analysis_result_id: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime
    message_count: Optional[int] = 0
    
    class Config:
        from_attributes = True


class ConversationDetailResponse(ConversationResponse):
    messages: List[ConversationMessageResponse]

