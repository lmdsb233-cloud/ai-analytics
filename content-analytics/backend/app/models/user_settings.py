import uuid
from datetime import datetime
from sqlalchemy import Column, String, ForeignKey, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.base import Base


class UserSettings(Base):
    """用户设置模型 - 存储用户的AI API配置"""
    __tablename__ = "user_settings"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), unique=True, nullable=False)
    
    # AI配置
    ai_provider = Column(String(50), default="deepseek")  # deepseek / openai / iflow
    deepseek_api_key = Column(Text, nullable=True)
    openai_api_key = Column(Text, nullable=True)
    iflow_api_key = Column(Text, nullable=True)
    iflow_model = Column(String(100), default="kimi-k2-0905")
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    user = relationship("User", backref="settings")
