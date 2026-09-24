from .minirag_base import SQLAlchemyBase
from sqlalchemy import Column, Integer, DateTime, func, String, ForeignKey, Text
from sqlalchemy.orm import relationship


class Message(SQLAlchemyBase):

    __tablename__ = "messages"

    message_id = Column(Integer, primary_key=True, autoincrement=True)
    message_conversation_id = Column(
        Integer,
        ForeignKey("conversations.conversation_id"),
        nullable=False,
    )
    role = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    conversation = relationship("Conversation", back_populates="messages")