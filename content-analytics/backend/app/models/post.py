import uuid
from datetime import datetime
from sqlalchemy import Column, String, Float, DateTime, ForeignKey, Text, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.base import Base


class Post(Base):
    __tablename__ = "posts"

    __table_args__ = (
        Index("ix_posts_dataset_id", "dataset_id"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    dataset_id = Column(UUID(as_uuid=True), ForeignKey("datasets.id"), nullable=False)
    
    # 原始字段
    data_id = Column(String(100), nullable=False, index=True)
    publish_time = Column(DateTime, nullable=True)
    publish_link = Column(String(500), nullable=True)
    content_type = Column(String(50), nullable=True)  # 内容形式
    post_type = Column(String(100), nullable=True)    # 发文类型
    source = Column(String(100), nullable=True)       # 素材来源
    style_info = Column(Text, nullable=True)          # 款式信息
    
    # 7天指标
    read_7d = Column(Float, nullable=True)       # 7天阅读/播放
    interact_7d = Column(Float, nullable=True)   # 7天互动
    visit_7d = Column(Float, nullable=True)      # 7天好物访问
    want_7d = Column(Float, nullable=True)       # 7天好物想要
    
    # 14天指标
    read_14d = Column(Float, nullable=True)      # 14天阅读/播放
    interact_14d = Column(Float, nullable=True)  # 14天互动
    visit_14d = Column(Float, nullable=True)     # 14天好物访问
    want_14d = Column(Float, nullable=True)      # 14天好物想要
    
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    dataset = relationship("Dataset", back_populates="posts")
    analysis_results = relationship("AnalysisResult", back_populates="post", cascade="all, delete-orphan")
