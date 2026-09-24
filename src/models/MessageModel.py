from .BaseModel import BaseDataModel
from .db_schemes import Message
from sqlalchemy import select


class MessageModel(BaseDataModel):

    def __init__(self, db_client: object):
        super().__init__(db_client=db_client)
        self.db_client = db_client

    @classmethod
    async def create_instance(cls, db_client: object):
        instance = cls(db_client)
        return instance

    async def create_message(self, message: Message):

        async with self.db_client() as session:
            async with session.begin():
                session.add(message)
            await session.commit()
            await session.refresh(message)
        return message

    async def get_recent_messages(self, conversation_id: int, limit: int = 20):

        async with self.db_client() as session:
            query = (
                select(Message)
                .where(Message.message_conversation_id == conversation_id)
                .order_by(Message.created_at.desc(), Message.message_id.desc())
                .limit(limit)
            )
            result = await session.execute(query)
            messages = result.scalars().all()

        return list(reversed(messages))