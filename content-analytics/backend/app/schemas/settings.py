from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from datetime import datetime


class SettingsUpdate(BaseModel):
    """更新设置请求"""
    ai_provider: Optional[str] = None
    deepseek_api_key: Optional[str] = None
    openai_api_key: Optional[str] = None
    iflow_api_key: Optional[str] = None
    iflow_model: Optional[str] = None


class SettingsResponse(BaseModel):
    """设置响应"""
    id: UUID
    user_id: UUID
    ai_provider: str
    has_deepseek_key: bool  # 不返回实际密钥，只返回是否已配置
    has_openai_key: bool
    has_iflow_key: bool
    iflow_model: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class SettingsCreate(BaseModel):
    """创建设置"""
    ai_provider: str = "deepseek"
    deepseek_api_key: Optional[str] = None
    openai_api_key: Optional[str] = None
    iflow_api_key: Optional[str] = None
    iflow_model: Optional[str] = "kimi-k2-0905"
