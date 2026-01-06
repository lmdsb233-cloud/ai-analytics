import uuid
from datetime import datetime
from enum import Enum as PyEnum
from sqlalchemy import Column, String, DateTime, ForeignKey, Enum, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.base import Base


class ExportFormat(str, PyEnum):
    EXCEL = "excel"
    PDF = "pdf"
    JSON = "json"


class ExportStatus(str, PyEnum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class Export(Base):
    __tablename__ = "exports"

    __table_args__ = (
        Index("ix_exports_user_id_created_at", "user_id", "created_at"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    analysis_id = Column(UUID(as_uuid=True), ForeignKey("analyses.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    file_path = Column(String(500), nullable=True)
    format = Column(Enum(ExportFormat, native_enum=False), default=ExportFormat.EXCEL)
    status = Column(Enum(ExportStatus, native_enum=False), default=ExportStatus.PENDING)
    error_message = Column(String(1000), nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    # Relationships
    analysis = relationship("Analysis", back_populates="exports")
    user = relationship("User", back_populates="exports")
