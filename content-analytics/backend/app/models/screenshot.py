from sqlalchemy import Column, String, Text, ForeignKey, JSON, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.db.base import Base


class ScreenshotAnalysis(Base):
    """截图分析记录表"""
    __tablename__ = "screenshot_analyses"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    image_path = Column(String(500), nullable=False, comment="图片存储路径")
    summary = Column(Text, comment="总结")
    strengths = Column(JSON, comment="优点列表")
    weaknesses = Column(JSON, comment="问题列表")
    suggestions = Column(JSON, comment="建议列表")
    model_name = Column(String(100), comment="使用的AI模型")
    tokens_used = Column(JSON, comment="Token使用情况")
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")

    # 关系
    user = relationship("User", back_populates="screenshot_analyses")