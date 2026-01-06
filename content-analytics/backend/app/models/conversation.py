import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Text, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from app.db.base import Base


class ConversationContextType:
    """对话上下文类型"""
    GENERAL = "general"
    ANALYSIS = "analysis"
    ANALYSIS_RESULT = "analysis_result"


class Conversation(Base):
    __tablename__ = "conversations"
    
    __table_args__ = (
        Index("ix_conversations_user_id_updated_at", "user_id", "updated_at"),
        Index("ix_conversations_context_analysis", "context_analysis_id"),
        Index("ix_conversations_context_result", "context_analysis_result_id"),
    )
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    title = Column(String(255), nullable=True)
    context_type = Column(String(20), default=ConversationContextType.GENERAL)
    context_analysis_id = Column(UUID(as_uuid=True), ForeignKey("analyses.id"), nullable=True)
    context_analysis_result_id = Column(UUID(as_uuid=True), ForeignKey("analysis_results.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="conversations")
    analysis = relationship("Analysis", foreign_keys=[context_analysis_id])
    analysis_result = relationship("AnalysisResult", foreign_keys=[context_analysis_result_id])
    messages = relationship(
        "ConversationMessage", 
        back_populates="conversation", 
        cascade="all, delete-orphan", 
        order_by="ConversationMessage.created_at"
    )


class ConversationMessage(Base):
    __tablename__ = "conversation_messages"
    
    __table_args__ = (
        Index("ix_conversation_messages_conversation_id", "conversation_id"),
        Index("ix_conversation_messages_created_at", "created_at"),
    )
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id"), nullable=False)
    role = Column(String(20), nullable=False)  # 'user' | 'assistant' | 'system'
    content = Column(Text, nullable=False)
    extra_data = Column(JSONB, nullable=True)  # 存储查询结果、数据ID等（原metadata，因SQLAlchemy保留字改名）
    tokens_used = Column(JSONB, nullable=True)
    model_name = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    conversation = relationship("Conversation", back_populates="messages")

