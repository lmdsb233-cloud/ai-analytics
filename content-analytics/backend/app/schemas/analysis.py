from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID


class AnalysisCreate(BaseModel):
    dataset_id: UUID
    name: Optional[str] = None
    config: Optional[Dict[str, Any]] = None


class AnalysisResponse(BaseModel):
    id: UUID
    dataset_id: UUID
    name: Optional[str] = None
    status: str
    progress: str
    error_message: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class AnalysisResultData(BaseModel):
    performance: str  # 偏高/正常/偏低
    problem_metrics: List[str] = []
    highlight_metrics: List[str] = []
    compare_to_avg: Dict[str, str] = {}


class AnalysisResultResponse(BaseModel):
    id: UUID
    analysis_id: UUID
    post_id: UUID
    performance: Optional[str] = None
    result_data: Optional[Dict[str, Any]] = None
    created_at: datetime
    
    # 关联的笔记基本信息
    post_data_id: Optional[str] = None
    post_content_type: Optional[str] = None
    post_type: Optional[str] = None

    class Config:
        from_attributes = True


class AIOutputResponse(BaseModel):
    id: UUID
    analysis_result_id: UUID
    summary: Optional[str] = None
    strengths: Optional[List[str]] = None
    weaknesses: Optional[List[str]] = None
    suggestions: Optional[List[str]] = None
    model_name: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class AnalysisDetailResponse(BaseModel):
    analysis: AnalysisResponse
    results: List[AnalysisResultResponse]
    total_results: int
