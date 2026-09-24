from .minirag_base import SQLAlchemyBase
from sqlalchemy import Column, Integer, DateTime, func, String, ForeignKey
from sqlalchemy.orm import relationship
import uuid
from sqlalchemy.dialects.postgresql import UUID


class Conversation(SQLAlchemyBase):

    __tablename__ = "conversations"

    conversation_id = Column(Integer, primary_key=True, autoincrement=True)
    conversation_uuid = Column(UUID(as_uuid=True), default=uuid.uuid4, unique=True, nullable=False)
    conversation_project_id = Column(Integer, ForeignKey("projects.project_id"), nullable=False)
    title = Column(String, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)

    project = relationship("Project", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")