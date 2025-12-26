import uuid
from datetime import datetime
from enum import Enum as PyEnum
from sqlalchemy import Column, String, DateTime, ForeignKey, Enum, Text, Index
from sqlalchemy.dialects.postgresql import UUID, JSON
from sqlalchemy.orm import relationship
from app.db.base import Base


class AnalysisStatus(str, PyEnum):
    PENDING = "pending"
    ANALYZING = "analyzing"
    AI_PROCESSING = "ai_processing"
    COMPLETED = "completed"
    FAILED = "failed"


class Analysis(Base):
    __tablename__ = "analyses"

    __table_args__ = (
        Index("ix_analyses_user_id_created_at", "user_id", "created_at"),
        Index(
            "ix_analyses_user_id_dataset_id_created_at",
            "user_id",
            "dataset_id",
            "created_at",
        ),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    dataset_id = Column(UUID(as_uuid=True), ForeignKey("datasets.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    name = Column(String(255), nullable=True)
    status = Column(Enum(AnalysisStatus), default=AnalysisStatus.PENDING)
    config = Column(JSON, nullable=True)  # 分析配置
    progress = Column(String(50), default="0%")
    error_message = Column(String(1000), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    # Relationships
    dataset = relationship("Dataset", back_populates="analyses")
    user = relationship("User", back_populates="analyses")
    results = relationship("AnalysisResult", back_populates="analysis", cascade="all, delete-orphan")
    exports = relationship("Export", back_populates="analysis", cascade="all, delete-orphan")


class AnalysisResult(Base):
    __tablename__ = "analysis_results"

    __table_args__ = (
        Index("ix_analysis_results_analysis_id_created_at", "analysis_id", "created_at"),
        Index("ix_analysis_results_analysis_id_performance", "analysis_id", "performance"),
        Index("ix_analysis_results_analysis_id_post_id", "analysis_id", "post_id"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    analysis_id = Column(UUID(as_uuid=True), ForeignKey("analyses.id"), nullable=False)
    post_id = Column(UUID(as_uuid=True), ForeignKey("posts.id"), nullable=False)
    
    # 分析结果
    performance = Column(String(20), nullable=True)  # 偏高/正常/偏低
    result_data = Column(JSON, nullable=True)  # 完整结构化分析结果
    
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    analysis = relationship("Analysis", back_populates="results")
    post = relationship("Post", back_populates="analysis_results")
    ai_output = relationship("AIOutput", back_populates="analysis_result", uselist=False, cascade="all, delete-orphan")


class AIOutput(Base):
    __tablename__ = "ai_outputs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    analysis_result_id = Column(UUID(as_uuid=True), ForeignKey("analysis_results.id"), nullable=False, unique=True)
    
    # AI分析结果
    summary = Column(Text, nullable=True)       # 一句话结论
    strengths = Column(JSON, nullable=True)     # 好在哪
    weaknesses = Column(JSON, nullable=True)    # 差在哪
    suggestions = Column(JSON, nullable=True)   # 优化建议
    
    # 原始响应和元数据
    raw_response = Column(Text, nullable=True)
    model_name = Column(String(50), nullable=True)
    tokens_used = Column(JSON, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    analysis_result = relationship("AnalysisResult", back_populates="ai_output")
